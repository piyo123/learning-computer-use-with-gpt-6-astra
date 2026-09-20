Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Form
$form = New-Object System.Windows.Forms.Form
$form.Text = "PowerShell Form Test"
$form.Size = New-Object System.Drawing.Size(400, 180)
$form.StartPosition = "CenterScreen"

# TextBox
$textBox = New-Object System.Windows.Forms.TextBox
$textBox.Location = New-Object System.Drawing.Point(30, 30)
$textBox.Size = New-Object System.Drawing.Size(320, 25)
$form.Controls.Add($textBox)

# Button
$button = New-Object System.Windows.Forms.Button
$button.Text = "Show"
$button.Location = New-Object System.Drawing.Point(30, 75)
$button.Size = New-Object System.Drawing.Size(100, 30)
$form.Controls.Add($button)

# Button click event
$button.Add_Click({
    [System.Windows.Forms.MessageBox]::Show(
        $textBox.Text,
        "Input Value"
    )
})

# Show form
[void]$form.ShowDialog()