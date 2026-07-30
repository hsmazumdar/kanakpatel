/*
 * ============================================================================
 * WSN Localization and Mapping Application
 * ============================================================================
 * 
 * Author:        Himanshu S Mazumdar
 * Date:          January 2026
 * Version:       1.0
 * 
 * Description:   Wireless Sensor Network (WSN) localization algorithm
 *                visualization and testing application. Implements a
 *                topology-preserving spatial consensus mechanism for
 *                anchor-free, range-free node localization.
 * 
 * License:       Copyright (c) 2026 Mazumdar
 *                All rights reserved.
 * 
 *                This software is provided for research and academic purposes.
 *                Permission is granted to use, copy, modify, and distribute
 *                this software for research and academic purposes, provided
 *                that the above copyright notice and this permission notice
 *                appear in all copies.
 * 
 *                THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 *                EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 *                OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 *                NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 *                HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 *                WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 *                FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 *                OTHER DEALINGS IN THE SOFTWARE.
 * 
 * ============================================================================
 */

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace WsnMap
{
    public partial class WsnMap : Form
    {
        //******************************************************
        private Point[] referenceNodes;
        private int[] referenceSequenceNumbers;
        private float[][] dstmtrxval; // distance matrix value in Tx Range
        private int[][] dstmtrxid;    // node numver of distance matrix 
        private Point[] localizedNodes;
        private int[] localizedSequenceNumbers;
        private int[] localizedRefMapping;
        private int txRange = 10; // Maximum number of neighbors to store
        private float txDistance; // Transmission range in pixels (calculated from numudTxRange % of canvas diagonal)
        private int nodSize = 20;
        private bool correct = false;
        private Random rnd = new Random(DateTime.Now.Millisecond);

        // RSS model parameters (log-normal shadowing)
        private double PL0 = -40.0; // Path loss at reference distance (dBm)
        private double d0 = 1.0; // Reference distance (meters)
        private double eta = 2.5; // Path loss exponent
        private double sigma = 4.0; // Shadowing standard deviation (dB)

        // Kernel-based self-correction parameters
        private double alpha = 0.1; // EWMA smoothing factor for RSS mean
        private double beta = 0.1; // EWMA smoothing factor for RSS variance
        private double epsilon = 0.01; // Small constant to prevent division by zero

        // Signal Kernel Table: [node][neighbor_index] -> KernelInfo
        private KernelInfo[][] kernelTable; // Kernel statistics for each node's neighbors

        // Localization algorithm counter
        private int localizationIterationCount = 0;
        private bool isLocalizationRunning = false;

        // Track which plot is currently displayed
        private bool isLocalizedNodesDisplayed = false;
        private int activeDisplayMode = 0; // 0 = reference nodes, 1 = localized nodes
        private bool finishFlag = false;
        private int count = 0; // itteration count
        //******************************************************

        // Signal Kernel structure for each neighbor
        private class KernelInfo
        {
            public double RssMean { get; set; }      // Exponentially weighted moving average of RSS
            public double RssVariance { get; set; }   // Estimated variance of RSS
            public double ConfidenceWeight { get; set; } // Confidence weight derived from mean and variance
        }

        // Helper class to store neighbor information during sorting
        private class NeighborInfo
        {
            public int NodeId { get; set; }
            public double Distance { get; set; }
            public float Rss { get; set; }
        }
        //******************************************************
        /// <summary>
        /// Constructor for WsnMap form. Initializes the Windows Forms components.
        /// </summary>
        public WsnMap()
        {
            InitializeComponent();
        }
        //******************************************************
        /// <summary>
        /// Event handler called when the form is first shown. Sets up the canvas,
        /// adjusts window size to fill screen, and initializes the node network.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void WsnMap_Shown(object sender, EventArgs e)
        {
            pbxCanvas.Location = new Point(0, 0);
            pbxCanvas.Size = pnlCanvas.Size;
            // Get screen working area (excludes taskbar)
            var screen = Screen.FromControl(this);
            var workingArea = screen.WorkingArea;
            this.Height = screen.WorkingArea.Height;
            this.Location = new Point(0, 0);
            var fw = this.Width;
            var gapx = fw - pbxCanvas.Width;
            this.Width = gapx + pbxCanvas.Height;
            // Stretch pictureWorld to fill panel
            pbxCanvas.Dock = DockStyle.Fill;
            ClearCanvas();
            referenceNodes = PopulateNodes();
            btnNodes_Click(null, null);
            //PopulateRssMatrix();
            // Initialize localized nodes as done by START button
            InitializeLocalizedNodes();
            PopulateDistanceMatrix();
            DrawNodes(referenceNodes, referenceSequenceNumbers, Color.Black);
        }
        //******************************************************
        private void PopulateDistanceMatrix()
        {
            //populate float[][] dstmtrxval and int[][] dstmtrxid of referenceNodes
            //populate float[][] dstmtrxval and int[][] dstmtrxid of referenceNodes
            if (referenceNodes == null || referenceNodes.Length == 0)
                return;

            // Calculate transmission distance from numudTxRange (% of canvas diagonal)
            CalculateTxDistance();

            int numNodes = referenceNodes.Length;

            // Initialize arrays
            dstmtrxval = new float[numNodes][];
            dstmtrxid = new int[numNodes][];

            // For each node
            for (int i = 0; i < numNodes; i++)
            {
                // List to store neighbors with distance
                List<NeighborInfo> neighbors = new List<NeighborInfo>();

                // Find all neighbors within transmission range
                for (int j = 0; j < numNodes; j++)
                {
                    if (i == j)
                        continue; // Skip self

                    // Calculate Euclidean distance
                    double dx = referenceNodes[i].X - referenceNodes[j].X;
                    double dy = referenceNodes[i].Y - referenceNodes[j].Y;
                    double distance = Math.Sqrt(dx * dx + dy * dy);

                    // Check if within transmission range
                    if (distance <= txDistance)
                    {
                        // Store neighbor information
                        neighbors.Add(new NeighborInfo
                        {
                            NodeId = j,
                            Distance = distance,
                            Rss = 0 // Not used for distance matrix
                        });
                    }
                }

                // Sort neighbors by distance (ascending order)
                neighbors.Sort((a, b) => a.Distance.CompareTo(b.Distance));

                // Store up to txRange neighbors (variable entries per node depending on TxRange)
                int neighborCount = Math.Min(neighbors.Count, txRange);
                dstmtrxval[i] = new float[neighborCount];
                dstmtrxid[i] = new int[neighborCount];

                for (int k = 0; k < neighborCount; k++)
                {
                    dstmtrxval[i][k] = (float)neighbors[k].Distance;
                    dstmtrxid[i][k] = neighbors[k].NodeId;
                }
            }
        }

        //******************************************************
        /// <summary>
        /// Clears the drawing canvas by creating a new black bitmap and assigning it to the picture box.
        /// </summary>
        /// <remarks>
        /// Disposes of graphics resources properly to prevent memory leaks.
        /// </remarks>
        private void ClearCanvas()
        {
            Bitmap bmp = new Bitmap(pbxCanvas.Width, pbxCanvas.Height);
            Graphics g = Graphics.FromImage(bmp);
            g.Clear(Color.Black);
            pbxCanvas.Image = bmp;
            g.Dispose();
        }
        //******************************************************
        /// <summary>
        /// Event handler called when the form size changes. Adjusts canvas size
        /// to match the panel and clears the canvas.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void WsnMap_SizeChanged(object sender, EventArgs e)
        {
            pbxCanvas.Size = pnlCanvas.Size;
            ClearCanvas();
        }
        //******************************************************
        /// <summary>
        /// Event handler for the Exit button. Stops the localization timer
        /// and closes the application.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void btnExit_Click(object sender, EventArgs e)
        {
            tmrLocalization.Stop();
            this.Close();
        }
        //******************************************************
        /// <summary>
        /// Event handler for the NODES button. Generates the reference node set and
        /// populates RSS matrices, initializes kernel tables, and starts the simulation timer.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        /// <remarks>
        /// Creates numNodes different random node configurations, each representing
        /// a different node's initial random map in the localization algorithm.
        /// </remarks>
        private void btnNodes_Click(object sender, EventArgs e)
        {
            referenceNodes = PopulateNodes();
            InitializeLocalizedNodes();
            int numNodes = referenceNodes.Length;
            referenceSequenceNumbers = new int[numNodes];
            for (int i = 0; i < numNodes; i++)
            {
                referenceSequenceNumbers[i] = i;
            }
            activeDisplayMode = 0;
            InitializeLocalizedNodes();
            PopulateDistanceMatrix();
            DrawNodes(referenceNodes, referenceSequenceNumbers, Color.Black);
            count = 0;
            // Populate RSS matrix
            //PopulateRssMatrix();//

            // Initialize kernel tables for all node sets
            //InitializeKernelTables();//
        }
        //******************************************************
        /// <summary>
        /// Generates a random spatial distribution of sensor nodes on the canvas.
        /// Uses a grid-based approach with random jitter within each grid cell.
        /// </summary>
        /// <returns>Array of Point structures representing node positions</returns>
        /// <remarks>
        /// Reads node count from txbxNodes textbox (default: 100). Calculates an
        /// approximately square grid, then places each node randomly within its grid cell.
        /// Ensures nodes stay within canvas bounds with proper margins.
        /// </remarks>
        private Point[] PopulateNodes()
        {
            int numNodes;
            if (!int.TryParse(txbxNodes.Text, out numNodes) || numNodes <= 0)
            {
                numNodes = 100; // Default value
            }
            int canvasWidth = pbxCanvas.Width;
            int canvasHeight = pbxCanvas.Height;

            // Calculate margin (2x nodeRadius on each side)
            int margin = nodSize;
            int usableWidth = canvasWidth - 1 * margin;
            int usableHeight = canvasHeight - 1 * margin;

            // Ensure usable area is valid
            if (usableWidth <= 0 || usableHeight <= 0)
            {
                return new Point[0];
            }

            // Calculate grid dimensions (approximately square grid)
            int gridCols = (int)Math.Ceiling(Math.Sqrt(numNodes));
            int gridRows = (int)Math.Ceiling((double)numNodes / gridCols);

            // Calculate cell dimensions within usable area
            double cellWidth = (double)usableWidth / gridCols;
            double cellHeight = (double)usableHeight / gridRows;

            Point[] nodes = new Point[numNodes];

            int nodeIndex = 0;
            for (int row = 0; row < gridRows && nodeIndex < numNodes; row++)
            {
                for (int col = 0; col < gridCols && nodeIndex < numNodes; col++)
                {
                    // Random position within the grid cell, within usable area
                    double x = -margin + col * cellWidth + rnd.NextDouble() * cellWidth;
                    double y = -margin + row * cellHeight + rnd.NextDouble() * cellHeight;

                    // Ensure nodes stay within usable bounds (with margin)
                    int nodeX = Math.Max(margin, Math.Min(canvasWidth - margin - 1, (int)x));
                    int nodeY = Math.Max(margin, Math.Min(canvasHeight - margin - 1, (int)y));

                    nodes[nodeIndex] = new Point(nodeX, nodeY);
                    nodeIndex++;
                }
            }
            return nodes;
        }
        //******************************************************
        /// <summary>
        /// Generates a randomly shuffled sequence of node indices (0 to numNodes-1).
        /// Performs extensive shuffling (100*numNodes iterations) to ensure thorough randomization.
        /// </summary>
        /// <returns>Array of integers containing a random permutation of 0 to numNodes-1</returns>
        /// <remarks>
        /// Used for testing routing algorithms with different node identity mappings.
        /// The sequence represents randomized node ordering for algorithm validation.
        /// </remarks>
        private int[] PopulateSNo()
        {
            // Create array with values 0 to numNodes-1
            int[] sno = new int[referenceNodes.Length];
            for (int i = 0; i < sno.Length; i++)
            {
                sno[i] = i;
            }

            // Shuffle 100*numNodes times
            for (int shuffle = 0; shuffle < 100 * sno.Length; shuffle++)
            {
                int i = rnd.Next(sno.Length);
                int j = rnd.Next(sno.Length);
                // Swap sno[i] and sno[j]
                int temp = sno[i];
                sno[i] = sno[j];
                sno[j] = temp;
            }

            return sno;
        }
        //*************************************************************
        /// <summary>
        /// Draws nodes on the canvas as outlined circles with yellow sequence numbers.
        /// Node colors are based on their original position in referenceNodes (via sequence number):
        /// Lower half of referenceNodes are drawn in green, upper half in pink to distinguish movement.
        /// This ensures nodes retain their color even when displayed in localizedNodes.
        /// Uses anti-aliasing for smooth rendering.
        /// </summary>
        /// <param name="nod">Array of Point structures representing node positions</param>
        /// <param name="sno">Array of integers representing sequence numbers to display</param>
        /// <param name="col">Background color for the canvas</param>
        /// <remarks>
        /// Draws each node as a circle at the specified position, with the sequence number
        /// centered inside. The number of nodes drawn is based on nod.Length to ensure
        /// consistent array indexing. Requires nod and sno arrays to have the same length.
        /// </remarks>
        public void DrawNodes(Point[] nod, int[] sno, Color col)
        {
            if (nod == null || nod.Length == 0)
                return;

            // Track which plot is displayed (check if nod is localizedNodes)
            isLocalizedNodesDisplayed = (nod == localizedNodes);

            Bitmap bmp = new Bitmap(pbxCanvas.Width, pbxCanvas.Height);
            Graphics g = Graphics.FromImage(bmp);
            g.Clear(col);
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            // Determine half point based on referenceNodes length (original node positions)
            int halfPoint = (referenceNodes != null && referenceNodes.Length > 0) ? referenceNodes.Length / 2 : nod.Length / 2;
            for (int i = 0; i < nod.Length; i++)
            {
                Point pos = nod[i];
                // Draw hollow (outlined) circle - color based on original position in referenceNodes
                // Use sequence number (sno[i]) to determine which half of referenceNodes the node belongs to
                int seqNo = sno[i];
                Color circleColor = (seqNo < halfPoint) ? Color.Green : Color.Pink;
                using (Pen pen = new Pen(circleColor, 2))
                {
                    g.DrawEllipse(pen, pos.X, pos.Y, nodSize, nodSize);
                }
                // Draw node number centered inside the circle
                string nodeNum = sno[i].ToString();
                using (Font font = new Font("Arial", 10, FontStyle.Bold))
                using (Brush textBrush = new SolidBrush(Color.Yellow))
                {
                    SizeF textSize = g.MeasureString(nodeNum, font);
                    float textX = pos.X + (nodSize - textSize.Width) / 2;
                    float textY = pos.Y + (nodSize - textSize.Height) / 2;
                    g.DrawString(nodeNum, font, textBrush, textX, textY);
                }
            }
            g.Dispose();
            pbxCanvas.Image = bmp;
          //  HighlightNode(0, Color.Turquoise);
        }
        //******************************************************
        /// <summary>
        /// Highlights a specific node by drawing a colored circle around it.
        /// Works with the currently displayed nodes (referenceNodes or localizedNodes based on activeDisplayMode flag).
        /// </summary>
        /// <param name="nodno">The node number (index) to highlight</param>
        /// <param name="col">Color for the highlight circle</param>
        public void HighlightNode(int nodno, Color col)
        {
            if (pbxCanvas == null || pbxCanvas.Image == null)
                return;

            // Determine which array to use and validate
            Point[] nodeArray = null;
            if (activeDisplayMode == 0)
            {
                if (referenceNodes == null || referenceNodes.Length == 0)
                    return;
                nodeArray = referenceNodes;
            }
            else
            {
                if (localizedNodes == null || localizedNodes.Length == 0)
                    return;
                nodeArray = localizedNodes;
            }

            // Validate node number
            if (nodno < 0 || nodno >= nodeArray.Length)
                return;

            // Get the current bitmap
            Bitmap bmp = (Bitmap)pbxCanvas.Image;
            Graphics g = Graphics.FromImage(bmp);
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

            // Get node position (this is the top-left corner of the node circle)
            Point nodePos = nodeArray[nodno];

            // Draw red circle around the node (larger than the node itself)
            // Node center is at (nodePos.X + nodSize/2, nodePos.Y + nodSize/2)
            // Highlight should be centered on the node, so calculate top-left of highlight circle
            int highlightRadius = nodSize + 10; // Make it larger than the node
            int highlightX = nodePos.X - 5; // Offset to center the larger circle around node
            int highlightY = nodePos.Y - 5;
            using (Pen redPen = new Pen(col, 3))
            {
                g.DrawEllipse(redPen, highlightX, highlightY, highlightRadius, highlightRadius);
            }

            g.Dispose();
            pbxCanvas.Image = bmp;
        }

        //******************************************************
        /// <summary>
        /// Calculates the transmission distance (txDistance) from the numudTxRange value.
        /// txDistance is set as a percentage of the canvas diagonal distance.
        /// </summary>
        /// <remarks>
        /// Formula: txDistance = (numudTxRange / 100.0) * canvasDiagonal
        /// Canvas diagonal = sqrt(canvasWidth² + canvasHeight²)
        /// </remarks>
        private void CalculateTxDistance()
        {
            if (pbxCanvas == null)
                return;

            // Calculate canvas diagonal distance
            double canvasWidth = pbxCanvas.Width;
            double canvasHeight = pbxCanvas.Height;
            double canvasDiagonal = Math.Sqrt(canvasWidth * canvasWidth + canvasHeight * canvasHeight);

            // Get percentage from numudTxRange (0-100)
            double percentage = (double)numudTxRange.Value / 100.0;

            // Calculate transmission distance as percentage of diagonal
            txDistance = (float)(percentage * canvasDiagonal);
        }

        //******************************************************
        /// <summary>
        /// Event handler called when the transmission range numeric up-down control value changes.
        /// Recalculates txDistance and repopulates the RSS matrix with the new transmission range.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void numudTxRange_ValueChanged(object sender, EventArgs e)
        {
            // Recalculate transmission distance
            CalculateTxDistance();
        }
        //******************************************************
        /// <summary>
        /// Initializes localizedNodes and localizedSequenceNumbers arrays. Re-initializes referenceNodes, creates localizedNodes
        /// with randomized sequence numbers, and populates RSS matrices.
        /// </summary>
        private void InitializeLocalizedNodes()
        {
            // 1. Re-initialize referenceNodes[] and draw
            referenceNodes = PopulateNodes();
            if (referenceSequenceNumbers == null || referenceSequenceNumbers.Length != referenceNodes.Length)
            {
                referenceSequenceNumbers = new int[referenceNodes.Length];
                for (int i = 0; i < referenceNodes.Length; i++)
                {
                    referenceSequenceNumbers[i] = i;
                }
            }
            DrawNodes(referenceNodes, referenceSequenceNumbers, Color.Black);

            // 2. Re-initialize localizedNodes[] and localizedSequenceNumbers[] (randomized sequence)
            localizedNodes = PopulateNodes();
            localizedSequenceNumbers = new int[localizedNodes.Length];
            localizedRefMapping = new int[localizedNodes.Length];

            // Initialize with sequential values
            for (int i = 0; i < localizedSequenceNumbers.Length; i++)
            {
                localizedSequenceNumbers[i] = i;
            }

            // Randomize: shuffle 100*numNodes times
            for (int shuffle = 0; shuffle < 100 * localizedSequenceNumbers.Length; shuffle++)
            {
                int i = rnd.Next(localizedSequenceNumbers.Length);
                int j = rnd.Next(localizedSequenceNumbers.Length);
                // Swap localizedSequenceNumbers[i] and localizedSequenceNumbers[j]
                int temp = localizedSequenceNumbers[i];
                localizedSequenceNumbers[i] = localizedSequenceNumbers[j];
                localizedSequenceNumbers[j] = temp;
            }

            for (int i = 0; i < localizedSequenceNumbers.Length; i++)
            {
                localizedRefMapping[localizedSequenceNumbers[i]] = i;
            }
            DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
        }
        //******************************************************
        /// <summary>
        /// Event handler for the START button. Toggles the localization timer on/off.
        /// When started, runs the localization algorithm to reposition localizedNodes.
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void btnStartLocalization_Click(object sender, EventArgs e)
        {
            if (isLocalizationRunning)
            {
                // Stop the timer
                tmrLocalization.Stop();
                isLocalizationRunning = false;
                btnStartLocalization.Text = "START";
            }
            else
            {
                // Start the timer
                if (localizedNodes == null || localizedNodes.Length == 0)
                {
                    InitializeLocalizedNodes();
                }
                localizationIterationCount = 0;
                tmrLocalization.Interval = 10; // 10 ms interval
                tmrLocalization.Start();
                isLocalizationRunning = true;
                btnStartLocalization.Text = "STOP";
                count = 0;
            }
        }
        //******************************************************
        /// <summary>
        /// Normalizes localizedNodes positions to 90% occupancy of the canvas.
        /// Finds the bounding box of current positions, scales and translates
        /// them to fit within 90% of canvas dimensions (centered).
        /// </summary>
        private void NormalizeLocalizedNodes()
        {
            if (localizedNodes == null || localizedNodes.Length == 0 || pbxCanvas == null)
                return;

            // Find bounding box of current positions
            int minX = localizedNodes[0].X, maxX = localizedNodes[0].X;
            int minY = localizedNodes[0].Y, maxY = localizedNodes[0].Y;

            for (int i = 1; i < localizedNodes.Length; i++)
            {
                if (localizedNodes[i].X < minX) minX = localizedNodes[i].X;
                if (localizedNodes[i].X > maxX) maxX = localizedNodes[i].X;
                if (localizedNodes[i].Y < minY) minY = localizedNodes[i].Y;
                if (localizedNodes[i].Y > maxY) maxY = localizedNodes[i].Y;
            }

            // Calculate current dimensions
            int currentWidth = maxX - minX;
            int currentHeight = maxY - minY;

            // Skip normalization if nodes are too close together or dimensions are invalid
            if (currentWidth <= 0 || currentHeight <= 0)
                return;

            // Calculate target dimensions (90% of canvas)
            int canvasWidth = pbxCanvas.Width;
            int canvasHeight = pbxCanvas.Height;
            int targetWidth = (int)(canvasWidth * 0.9);
            int targetHeight = (int)(canvasHeight * 0.9);

            // Calculate independent scale factors for X and Y axes
            double scaleX = (double)targetWidth / currentWidth;
            double scaleY = (double)targetHeight / currentHeight;

            // Calculate current center
            double currentCenterX = (minX + maxX) / 2.0;
            double currentCenterY = (minY + maxY) / 2.0;

            // Calculate target center (center of canvas)
            double targetCenterX = canvasWidth / 2.0;
            double targetCenterY = canvasHeight / 2.0;

            // Calculate independent offsets
            double offsetX = targetCenterX - currentCenterX * scaleX;
            double offsetY = targetCenterY - currentCenterY * scaleY;

            // Apply transformation: independent scale and offset for X and Y
            for (int i = 0; i < localizedNodes.Length; i++)
            {
                // Apply independent scaling and offset for X axis
                double x = localizedNodes[i].X * scaleX + offsetX;

                // Apply independent scaling and offset for Y axis
                double y = localizedNodes[i].Y * scaleY + offsetY;

                // Update position
                localizedNodes[i] = new Point((int)x, (int)y);
            }
        }

        //******************************************************
        /// <summary>
        /// Event handler for the localization timer tick. On each tick:
        /// 1. Selects a random node
        /// 2. Repositions it in localizedNodes using weighted centroid of its neighbors from rssmtrxval and rssmtrxid
        /// 3. Draws localizedNodes
        /// 4. Updates the counter
        /// </summary>
        /// <param name="sender">The event sender</param>
        /// <param name="e">Event arguments</param>
        private void tmrLocalization_Tick(object sender, EventArgs e)
        {
            // Assume complete until a move is needed
            finishFlag = true;
            for (int i = 0; i < 100; i++)
            {
                // Select a random node to reposition
                activeDisplayMode = 1; // Ensure we're working with localizedNodes
                int arrayIndex = rnd.Next(localizedNodes.Length);
                MoveNodeByIndex(arrayIndex);
            }
            //Rotate45Degrees(localizedNodes);
            NormalizeLocalizedNodes();
            DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
            if (finishFlag == true)
            {
                // Localization completed: stop timer and show START again
                tmrLocalization.Stop();
                isLocalizationRunning = false;
                btnStartLocalization.Text = "START";
            }
            else
            {
                count++;
                lblCount.Text = count.ToString();
            }
        }
        //******************************************************
        /// <summary>
        /// Determines which node (if any) was clicked at the given mouse position.
        /// Checks if the mouse point is within any node's circle boundary.
        /// </summary>
        /// <param name="mousePos">The mouse click position (Point)</param>
        /// <returns>The index of the clicked node, or -1 if no node was clicked</returns>
        /// <remarks>
        /// Checks both referenceNodes and localizedNodes arrays. If localizedNodes is available, it uses that;
        /// otherwise falls back to referenceNodes. Nodes are drawn as circles with nodSize diameter,
        /// so the method checks if the mouse point is within the circle's radius.
        /// </remarks>
        private int GetNodeNumber(Point mousePos)
        {
            Point[] nodesToCheck = null;
            // Determine which node array to check based on activeDisplayMode flag
            if (activeDisplayMode == 1)
                nodesToCheck = localizedNodes;
            else
                nodesToCheck = referenceNodes;

            // Return -1 if array is null or empty
            if (nodesToCheck == null || nodesToCheck.Length == 0)
                return -1;

            // Calculate node radius (nodes are circles with nodSize diameter)
            double nodeRadius = nodSize / 2.0;
            // Check each node to see if mouse point is within its circle
            for (int i = 0; i < nodesToCheck.Length; i++)
            {
                Point nodePos = nodesToCheck[i];
                // Calculate center of the node circle
                double centerX = nodePos.X + nodeRadius;
                double centerY = nodePos.Y + nodeRadius;
                // Calculate distance from mouse point to node center
                double dx = mousePos.X - centerX;
                double dy = mousePos.Y - centerY;
                double distance = Math.Sqrt(dx * dx + dy * dy);
                // If distance is within radius, this node was clicked
                if (distance <= nodeRadius)
                    return i;
            }
            return -1;// No node was clicked
        }
        //******************************************************
        private void pbxCanvas_MouseDown(object sender, MouseEventArgs e)
        {
            Point mousePos = new Point(e.X, e.Y);
            MoveNode(mousePos);
        }
        //******************************************************
        /// <summary>
        /// Moves a node by its array index (for timer-based repositioning).
        /// Calculates centroid of neighbors and moves the node there.
        /// </summary>
        /// <param name="arrayIndex">The array index of the node in localizedNodes</param>
        private void MoveNodeByIndexOLD(int arrayIndex)
        {
            if (arrayIndex < 0 || arrayIndex >= localizedNodes.Length)
                return;

            if (activeDisplayMode != 1)
                return;

            int no2 = arrayIndex; // Array index in localizedNodes
            int seqNo = localizedSequenceNumbers[arrayIndex]; // Sequence number for distance matrix lookup

            float[] nbrval = dstmtrxval[seqNo];
            int[] nbrid = dstmtrxid[seqNo];

            // Calculate centroid of neighbors
            Point cg = new Point(0, 0);
            int mxno = Math.Min(nbrid.Length, nbrid.Length);
            for (int k = 0; k < mxno; k++)
            {
                int neighborSeqNo = nbrid[k];
                // Find array index of neighbor from its sequence number
                int neighborArrayIndex = -1;
                for (int i = 0; i < localizedSequenceNumbers.Length; i++)
                {
                    if (localizedSequenceNumbers[i] == neighborSeqNo)
                    {
                        neighborArrayIndex = i;
                        break;
                    }
                }
                if (neighborArrayIndex >= 0)
                {
                    cg.X += localizedNodes[neighborArrayIndex].X;
                    cg.Y += localizedNodes[neighborArrayIndex].Y;
                }
            }

            if (mxno == 0)
                return;

            cg.X /= mxno;
            cg.Y /= mxno;
            Point pto = localizedNodes[arrayIndex];
            // Calculate error distance (absolute distance from current position to centroid)
            float errorX = Math.Abs(cg.X - pto.X);
            float errorY = Math.Abs(cg.Y - pto.Y);
            float errorDistance = (float)Math.Sqrt(errorX * errorX + errorY * errorY);

            // Movement proportional to error - scale factor (adjust as needed)
            float scaleFactor = 0.01f; // Proportional scaling constant
            float movementScale = errorDistance * scaleFactor;

            // Direction vector from current position to centroid
            float dirX = cg.X - pto.X;
            float dirY = cg.Y - pto.Y;

            // Normalize direction vector and scale by error-proportional movement
            if (errorDistance > 0.0001f) // Avoid division by zero
            {
                float normalizedX = dirX / errorDistance;
                float normalizedY = dirY / errorDistance;
                float x = normalizedX * movementScale;
                float y = normalizedY * movementScale;
                // Move localizedNodes[arrayIndex] toward centroid (proportional to error distance)
                localizedNodes[arrayIndex] = new Point((int)(pto.X + x), (int)(pto.Y + y));
            }
        }

        //******************************************************
        /// <summary>
        /// Moves a node by its array index (for timer-based repositioning).
        /// Calculates centroid of neighbors and moves the node there.
        /// </summary>
        /// <param name="arrayIndex">The array index of the node in localizedNodes</param>
        private void MoveNodeByIndex(int arrayIndex)
        {
            if (arrayIndex < 0 || arrayIndex >= localizedNodes.Length)
                return;

            if (activeDisplayMode != 1)
                return;

            int no2 = arrayIndex; // Array index in localizedNodes
            int seqNo = localizedSequenceNumbers[arrayIndex]; // Sequence number for distance matrix lookup

            float[] nbrval = dstmtrxval[seqNo];
            int[] nbrid = dstmtrxid[seqNo];
            int mxno = Math.Min(nbrid.Length, nbrid.Length);

            //HighlightNode(no2, Color.Red);
           // pbxCanvas.Refresh();

            //for (int k = 0; k < mxno; k++)
            //{
            //    int neighborId = nbrid[k];
            //    neighborId = localizedRefMapping[neighborId];
            //    HighlightNode(neighborId, Color.Brown);
            //    pbxCanvas.Refresh();
            //}
            if (activeDisplayMode == 1)
            {// Move 
                Point selectedNodePos = localizedNodes[no2];
                //HighlightNode(no2, Color.Blue);
                //pbxCanvas.Refresh();

                for (int k = 0; k < mxno; k++)
                {
                    int neighborId = nbrid[k];
                    neighborId = localizedRefMapping[neighborId];
                    Point neighborPos = localizedNodes[neighborId];
                    
                    // Get expected distance from distance matrix
                    float expectedDistance = nbrval[k];
                    
                    // Calculate current actual distance between selected node and neighbor
                    double dx = selectedNodePos.X - neighborPos.X;
                    double dy = selectedNodePos.Y - neighborPos.Y;
                    double currentDistance = Math.Sqrt(dx * dx + dy * dy);

                    // Stop moving if neighbor is already within or at its expected distance from distance matrix
                    if (currentDistance <= expectedDistance)
                    {
                        continue;
                    }
                    // Still needs adjustment — not finished yet
                    finishFlag = false;
                    // Calculate 30% attraction towards selected node
                    int newX = (int)(neighborPos.X + 0.3f * (selectedNodePos.X - neighborPos.X));
                    int newY = (int)(neighborPos.Y + 0.3f * (selectedNodePos.Y - neighborPos.Y));
                    localizedNodes[neighborId] = new Point(newX, newY);
                }
            }
            //if (activeDisplayMode == 0)
            //{
            //    DrawNodes(referenceNodes, referenceSequenceNumbers, Color.FromArgb(0, 0, 64));
            //}
            //else
            //{
            //    DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
            //}



        }
        //******************************************************
        private void MoveNode(Point mousePos)
        {
            int no = GetNodeNumber(mousePos);
            int no2 = no;
            HighlightNode(no, Color.Red);
            pbxCanvas.Refresh();
            if (no >= 0)
            {
                if (activeDisplayMode == 1)
                    no = localizedSequenceNumbers[no];
                float[] nbrval = dstmtrxval[no];
                int[] nbrid = dstmtrxid[no];
                // Highlight neighbors in brown rings (limit to txRange nearest)
                Point cg = new Point(0, 0);
                int mxno = Math.Min(nbrid.Length, nbrid.Length);
                for (int k = 0; k < mxno; k++)
                {
                    int neighborId = nbrid[k];
                    if (activeDisplayMode == 1)
                        neighborId = localizedRefMapping[neighborId];
                    HighlightNode(neighborId, Color.Brown);
                    pbxCanvas.Refresh();
                    //calculate CG of neighbors
                    cg.X += localizedNodes[neighborId].X;
                    cg.Y += localizedNodes[neighborId].Y;
                }
                if (nbrid.Length == 0)
                    return;
                cg.X /= mxno;
                cg.Y /= mxno;
                if (correct == true)
                {
                    // Perform self-correction for the selected node
                    Console.WriteLine($"Performing self-correction for node {no}");
                    DrawCircle(cg, Color.Yellow);//draw a circle at cg
                    if (activeDisplayMode == 1)
                    {// Move localizedNodes[no] to cg
                     //  localizedNodes[no2] = new Point(cg.X, cg.Y);
                     // Attract brown neighbors 10% towards the mouse selected node
                        Point selectedNodePos = localizedNodes[no2];
                        HighlightNode(no2, Color.Blue);
                        pbxCanvas.Refresh();

                        for (int k = 0; k < mxno; k++)
                        {
                            int neighborId = nbrid[k];
                            neighborId = localizedRefMapping[neighborId];
                            Point neighborPos = localizedNodes[neighborId];
                            
                            // Get expected distance from distance matrix
                            float expectedDistance = nbrval[k];
                            
                            // Calculate current actual distance between selected node and neighbor
                            double dx = selectedNodePos.X - neighborPos.X;
                            double dy = selectedNodePos.Y - neighborPos.Y;
                            double currentDistance = Math.Sqrt(dx * dx + dy * dy);
                            
                            // Stop moving if neighbor is already within or at its expected distance from distance matrix
                            if (currentDistance <= expectedDistance)
                                continue;
                            
                            // Calculate 10% attraction towards selected node
                            int newX = (int)(neighborPos.X + 0.1f * (selectedNodePos.X - neighborPos.X));
                            int newY = (int)(neighborPos.Y + 0.1f * (selectedNodePos.Y - neighborPos.Y));
                            localizedNodes[neighborId] = new Point(newX, newY);
                        }
                    }
                }
            }
            pbxCanvas.Refresh();
        }
        //******************************************************
        private void DrawCircle(Point cg, Color col)
        {
            Bitmap bmp = (Bitmap)pbxCanvas.Image;
            Graphics g = Graphics.FromImage(bmp);
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            int highlightRadius = nodSize + 10; // Make it larger than the node
            int highlightX = cg.X - 5; // Offset to center the larger circle around node
            int highlightY = cg.Y - 5;
            using (Pen redPen = new Pen(col, 3))
            {
                g.DrawEllipse(redPen, highlightX, highlightY, highlightRadius, highlightRadius);
            }
            g.Dispose();
            pbxCanvas.Image = bmp;
            pbxCanvas.Refresh();
        }

        //******************************************************
        private void pbxCanvas_MouseUp(object sender, MouseEventArgs e)
        {
            if (activeDisplayMode == 0)
            {
                DrawNodes(referenceNodes, referenceSequenceNumbers, Color.FromArgb(0, 0, 64));
            }
            else
            {
                DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
            }
        }
        //******************************************************
        private void btnReferenceNodes_Click(object sender, EventArgs e)
        {
            activeDisplayMode = 0;
            DrawNodes(referenceNodes, referenceSequenceNumbers, Color.FromArgb(0, 0, 64));
        }
        //******************************************************
        private void btnLocalizedNodes_Click(object sender, EventArgs e)
        {
            activeDisplayMode = 1;
            DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
        }
        //******************************************************
        private void chkSelfCorrect_CheckedChanged(object sender, EventArgs e)
        {
            if (chkSelfCorrect.Checked)
            {
                correct = true;
                activeDisplayMode = 1;
                DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
            }
            else
            {
                correct = false;
            }
        }
        //******************************************************
        private void btnNormalize_Click(object sender, EventArgs e)
        {
            // Normalize localizedNodes positions to 90% occupancy of canvas
            if (localizedNodes == null || localizedNodes.Length == 0)
            {
                InitializeLocalizedNodes();
            }
            NormalizeLocalizedNodes();
            activeDisplayMode = 1;
            DrawNodes(localizedNodes, localizedSequenceNumbers, Color.Black);
        }
        //******************************************************123
    }
}
