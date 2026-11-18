param([string]$src,[string]$dst,[int]$max=1800)
Add-Type -AssemblyName System.Drawing
$img=[System.Drawing.Image]::FromFile($src)
$w=$img.Width;$h=$img.Height
$s=[Math]::Min(1.0,$max/[double][Math]::Max($w,$h))
$nw=[int]($w*$s);$nh=[int]($h*$s)
$bmp=New-Object System.Drawing.Bitmap($nw,$nh)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.Clear([System.Drawing.Color]::White)
$g.DrawImage($img,0,0,$nw,$nh)
$codec=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders()|?{$_.MimeType -eq 'image/jpeg'}
$ep=New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0]=New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality,[long]84)
$bmp.Save($dst,$codec,$ep)
"$nw x $nh"
$g.Dispose();$bmp.Dispose();$img.Dispose()
