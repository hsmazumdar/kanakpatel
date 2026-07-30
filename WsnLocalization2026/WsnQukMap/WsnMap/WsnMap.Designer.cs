namespace WsnMap
{
    partial class WsnMap
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.pnlCanvas = new System.Windows.Forms.Panel();
            this.pbxCanvas = new System.Windows.Forms.PictureBox();
            this.btnExit = new System.Windows.Forms.Button();
            this.btnNodes = new System.Windows.Forms.Button();
            this.txbxNodes = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.tmrLocalization = new System.Windows.Forms.Timer(this.components);
            this.label3 = new System.Windows.Forms.Label();
            this.numudTxRange = new System.Windows.Forms.NumericUpDown();
            this.btnStartLocalization = new System.Windows.Forms.Button();
            this.lblCount = new System.Windows.Forms.Label();
            this.chkSelfCorrect = new System.Windows.Forms.CheckBox();
            this.btnReferenceNodes = new System.Windows.Forms.Button();
            this.btnLocalizedNodes = new System.Windows.Forms.Button();
            this.btnNormalize = new System.Windows.Forms.Button();
            this.pnlCanvas.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.pbxCanvas)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numudTxRange)).BeginInit();
            this.SuspendLayout();
            // 
            // pnlCanvas
            // 
            this.pnlCanvas.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.pnlCanvas.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.pnlCanvas.Controls.Add(this.pbxCanvas);
            this.pnlCanvas.Location = new System.Drawing.Point(6, 6);
            this.pnlCanvas.Margin = new System.Windows.Forms.Padding(2);
            this.pnlCanvas.Name = "pnlCanvas";
            this.pnlCanvas.Size = new System.Drawing.Size(401, 417);
            this.pnlCanvas.TabIndex = 0;
            // 
            // pbxCanvas
            // 
            this.pbxCanvas.Location = new System.Drawing.Point(2, 2);
            this.pbxCanvas.Margin = new System.Windows.Forms.Padding(2);
            this.pbxCanvas.Name = "pbxCanvas";
            this.pbxCanvas.Size = new System.Drawing.Size(220, 219);
            this.pbxCanvas.TabIndex = 0;
            this.pbxCanvas.TabStop = false;
            this.pbxCanvas.MouseDown += new System.Windows.Forms.MouseEventHandler(this.pbxCanvas_MouseDown);
            this.pbxCanvas.MouseUp += new System.Windows.Forms.MouseEventHandler(this.pbxCanvas_MouseUp);
            // 
            // btnExit
            // 
            this.btnExit.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.btnExit.Location = new System.Drawing.Point(409, 399);
            this.btnExit.Margin = new System.Windows.Forms.Padding(2);
            this.btnExit.Name = "btnExit";
            this.btnExit.Size = new System.Drawing.Size(92, 23);
            this.btnExit.TabIndex = 1;
            this.btnExit.Text = "OK";
            this.btnExit.UseVisualStyleBackColor = true;
            this.btnExit.Click += new System.EventHandler(this.btnExit_Click);
            // 
            // btnNodes
            // 
            this.btnNodes.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnNodes.Location = new System.Drawing.Point(412, 87);
            this.btnNodes.Margin = new System.Windows.Forms.Padding(2);
            this.btnNodes.Name = "btnNodes";
            this.btnNodes.Size = new System.Drawing.Size(92, 23);
            this.btnNodes.TabIndex = 2;
            this.btnNodes.Text = "NODES";
            this.btnNodes.UseVisualStyleBackColor = true;
            this.btnNodes.Click += new System.EventHandler(this.btnNodes_Click);
            // 
            // txbxNodes
            // 
            this.txbxNodes.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.txbxNodes.Location = new System.Drawing.Point(412, 62);
            this.txbxNodes.Margin = new System.Windows.Forms.Padding(2);
            this.txbxNodes.Multiline = true;
            this.txbxNodes.Name = "txbxNodes";
            this.txbxNodes.Size = new System.Drawing.Size(94, 21);
            this.txbxNodes.TabIndex = 3;
            this.txbxNodes.Text = "100";
            this.txbxNodes.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // label1
            // 
            this.label1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(437, 46);
            this.label1.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(38, 13);
            this.label1.TabIndex = 4;
            this.label1.Text = "Nodes";
            // 
            // tmrLocalization
            // 
            this.tmrLocalization.Interval = 1000;
            this.tmrLocalization.Tick += new System.EventHandler(this.tmrLocalization_Tick);
            // 
            // label3
            // 
            this.label3.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(424, 8);
            this.label3.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(65, 13);
            this.label3.TabIndex = 10;
            this.label3.Text = "Tx Range %";
            // 
            // numudTxRange
            // 
            this.numudTxRange.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.numudTxRange.Location = new System.Drawing.Point(412, 24);
            this.numudTxRange.Name = "numudTxRange";
            this.numudTxRange.Size = new System.Drawing.Size(91, 20);
            this.numudTxRange.TabIndex = 9;
            this.numudTxRange.Value = new decimal(new int[] {
            15,
            0,
            0,
            0});
            this.numudTxRange.ValueChanged += new System.EventHandler(this.numudTxRange_ValueChanged);
            // 
            // btnStartLocalization
            // 
            this.btnStartLocalization.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnStartLocalization.Location = new System.Drawing.Point(411, 269);
            this.btnStartLocalization.Margin = new System.Windows.Forms.Padding(2);
            this.btnStartLocalization.Name = "btnStartLocalization";
            this.btnStartLocalization.Size = new System.Drawing.Size(92, 23);
            this.btnStartLocalization.TabIndex = 11;
            this.btnStartLocalization.Text = "START";
            this.btnStartLocalization.UseVisualStyleBackColor = true;
            this.btnStartLocalization.Click += new System.EventHandler(this.btnStartLocalization_Click);
            // 
            // lblCount
            // 
            this.lblCount.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.lblCount.AutoSize = true;
            this.lblCount.Location = new System.Drawing.Point(414, 112);
            this.lblCount.Margin = new System.Windows.Forms.Padding(2, 0, 2, 0);
            this.lblCount.Name = "lblCount";
            this.lblCount.Size = new System.Drawing.Size(38, 13);
            this.lblCount.TabIndex = 12;
            this.lblCount.Text = "Count:";
            // 
            // chkSelfCorrect
            // 
            this.chkSelfCorrect.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.chkSelfCorrect.AutoSize = true;
            this.chkSelfCorrect.Location = new System.Drawing.Point(410, 219);
            this.chkSelfCorrect.Margin = new System.Windows.Forms.Padding(2);
            this.chkSelfCorrect.Name = "chkSelfCorrect";
            this.chkSelfCorrect.Size = new System.Drawing.Size(95, 17);
            this.chkSelfCorrect.TabIndex = 13;
            this.chkSelfCorrect.Text = "Self-Correction";
            this.chkSelfCorrect.UseVisualStyleBackColor = true;
            this.chkSelfCorrect.CheckedChanged += new System.EventHandler(this.chkSelfCorrect_CheckedChanged);
            // 
            // btnReferenceNodes
            // 
            this.btnReferenceNodes.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnReferenceNodes.Location = new System.Drawing.Point(412, 165);
            this.btnReferenceNodes.Margin = new System.Windows.Forms.Padding(2);
            this.btnReferenceNodes.Name = "btnReferenceNodes";
            this.btnReferenceNodes.Size = new System.Drawing.Size(92, 23);
            this.btnReferenceNodes.TabIndex = 14;
            this.btnReferenceNodes.Text = "REFERENCE";
            this.btnReferenceNodes.UseVisualStyleBackColor = true;
            this.btnReferenceNodes.Click += new System.EventHandler(this.btnReferenceNodes_Click);
            // 
            // btnLocalizedNodes
            // 
            this.btnLocalizedNodes.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnLocalizedNodes.Location = new System.Drawing.Point(412, 192);
            this.btnLocalizedNodes.Margin = new System.Windows.Forms.Padding(2);
            this.btnLocalizedNodes.Name = "btnLocalizedNodes";
            this.btnLocalizedNodes.Size = new System.Drawing.Size(92, 23);
            this.btnLocalizedNodes.TabIndex = 15;
            this.btnLocalizedNodes.Text = "LOCALIZED";
            this.btnLocalizedNodes.UseVisualStyleBackColor = true;
            this.btnLocalizedNodes.Click += new System.EventHandler(this.btnLocalizedNodes_Click);
            // 
            // btnNormalize
            // 
            this.btnNormalize.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnNormalize.Location = new System.Drawing.Point(412, 240);
            this.btnNormalize.Margin = new System.Windows.Forms.Padding(2);
            this.btnNormalize.Name = "btnNormalize";
            this.btnNormalize.Size = new System.Drawing.Size(92, 23);
            this.btnNormalize.TabIndex = 16;
            this.btnNormalize.Text = "NORMALIZE";
            this.btnNormalize.UseVisualStyleBackColor = true;
            this.btnNormalize.Click += new System.EventHandler(this.btnNormalize_Click);
            // 
            // WsnMap
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(508, 430);
            this.Controls.Add(this.btnNormalize);
            this.Controls.Add(this.btnLocalizedNodes);
            this.Controls.Add(this.btnReferenceNodes);
            this.Controls.Add(this.chkSelfCorrect);
            this.Controls.Add(this.lblCount);
            this.Controls.Add(this.btnStartLocalization);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.numudTxRange);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.txbxNodes);
            this.Controls.Add(this.btnNodes);
            this.Controls.Add(this.btnExit);
            this.Controls.Add(this.pnlCanvas);
            this.Margin = new System.Windows.Forms.Padding(2);
            this.Name = "WsnMap";
            this.Text = "WSN Localization - Mazumdar";
            this.Shown += new System.EventHandler(this.WsnMap_Shown);
            this.SizeChanged += new System.EventHandler(this.WsnMap_SizeChanged);
            this.pnlCanvas.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.pbxCanvas)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numudTxRange)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Panel pnlCanvas;
        private System.Windows.Forms.PictureBox pbxCanvas;
        private System.Windows.Forms.Button btnExit;
        private System.Windows.Forms.Button btnNodes;
        private System.Windows.Forms.TextBox txbxNodes;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Timer tmrLocalization;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.NumericUpDown numudTxRange;
        private System.Windows.Forms.Button btnStartLocalization;
        private System.Windows.Forms.Label lblCount;
        private System.Windows.Forms.CheckBox chkSelfCorrect;
        private System.Windows.Forms.Button btnReferenceNodes;
        private System.Windows.Forms.Button btnLocalizedNodes;
        private System.Windows.Forms.Button btnNormalize;
    }
}

