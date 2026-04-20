$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "Presentation"
$outPptx = Join-Path $outDir "Milestone_6_Updated.pptx"
$tmp = Join-Path $env:TEMP ("nutrivision_pptx_" + [guid]::NewGuid().ToString("N"))

function E([string]$s) {
    return [System.Security.SecurityElement]::Escape($s)
}

function Emu([double]$inches) {
    return [int64]($inches * 914400)
}

function Add-Part([string]$path, [string]$content) {
    $full = Join-Path $tmp $path
    $dir = Split-Path -Parent $full
    if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText($full, $content, [System.Text.Encoding]::UTF8)
}

function Copy-Part([string]$source, [string]$path) {
    $full = Join-Path $tmp $path
    $dir = Split-Path -Parent $full
    if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item -LiteralPath $source -Destination $full -Force
}

function TextBox([int]$id, [string]$name, [double]$x, [double]$y, [double]$w, [double]$h, [string[]]$lines, [int]$fontSize = 22, [string]$color = "263238", [bool]$bold = $false) {
    $paras = New-Object System.Collections.Generic.List[string]
    $b = if ($bold) { ' b="1"' } else { '' }
    foreach ($line in $lines) {
        if ($line.Trim().Length -eq 0) {
            $paras.Add('<a:p><a:endParaRPr lang="en-US"/></a:p>')
        } else {
            $paras.Add('<a:p><a:r><a:rPr lang="en-US" sz="' + ($fontSize * 100) + '"' + $b + '><a:solidFill><a:srgbClr val="' + $color + '"/></a:solidFill></a:rPr><a:t>' + (E $line) + '</a:t></a:r></a:p>')
        }
    }
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$id" name="$(E $name)"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$(Emu $x)" y="$(Emu $y)"/><a:ext cx="$(Emu $w)" cy="$(Emu $h)"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>
  <p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>$($paras -join "")
  </p:txBody>
</p:sp>
"@
}

function RectShape([int]$id, [double]$x, [double]$y, [double]$w, [double]$h, [string]$fill, [string]$line = "FFFFFF") {
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$id" name="Block $id"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$(Emu $x)" y="$(Emu $y)"/><a:ext cx="$(Emu $w)" cy="$(Emu $h)"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="$fill"/></a:solidFill><a:ln w="9525"><a:solidFill><a:srgbClr val="$line"/></a:solidFill></a:ln></p:spPr>
</p:sp>
"@
}

function Picture([int]$id, [int]$relIdNum, [double]$x, [double]$y, [double]$w, [double]$h) {
    return @"
<p:pic>
  <p:nvPicPr><p:cNvPr id="$id" name="Image $id"/><p:cNvPicPr><a:picLocks noChangeAspect="0"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="rId$relIdNum"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="$(Emu $x)" y="$(Emu $y)"/><a:ext cx="$(Emu $w)" cy="$(Emu $h)"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>
"@
}

function SlideXml([string]$shapes) {
    return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="F7FAF8"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      $shapes
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"@
}

function SlideRels([string[]]$rels) {
    $body = '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    foreach ($rel in $rels) { $body += $rel }
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + $body + '</Relationships>'
}

if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$imageDir = Join-Path $root "Report\Images"
$appImage = Join-Path $imageDir "ds1.jpg"
$outputImage = Join-Path $imageDir "ds4.jpg"
$signImage = Join-Path $imageDir "sign.jpg"
$teamImages = @(
    @{Name="Sahil Raj"; Path=(Join-Path $imageDir "sahil_raj.jpeg"); Role="EDA, model training, tuning, evaluation, final deployment, technical report"},
    @{Name="Sahil Sharma"; Path=(Join-Path $imageDir "sahil.jpeg"); Role="Dataset processing, model evaluation, deployment pipeline, deployed system"},
    @{Name="Aman Mani Tiwari"; Path=(Join-Path $imageDir "aman.jpeg"); Role="EDA, reports, documentation, user guide"},
    @{Name="Tasneem Shahnawaz"; Path=(Join-Path $imageDir "tasneem.jpeg"); Role="Nutrition mapping, conversational layer, model training, non-technical report, README"},
    @{Name="Samreen Fathima"; Path=(Join-Path $imageDir "me.jpeg"); Role="Dataset analysis, model training, developer guide, codebase support"}
)

$slides = New-Object System.Collections.Generic.List[hashtable]

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.75 0.75 11.8 1.2 @("NutriVision", "AI-Powered Indian Food Nutrition Estimator") 38 "114B3A" $true) +
    (TextBox 3 "Subtitle" 0.8 2.25 11.5 1.0 @("Milestone 6 Updated Presentation", "Final pipeline, web app, reports, results, and team contributions") 24 "263238" $false) +
    (RectShape 4 0.8 4.2 3.0 0.75 "DDEFE6" "7BAE92") + (TextBox 5 "Badge1" 1.05 4.38 2.7 0.4 @("79 Indian food classes") 18 "114B3A" $true) +
    (RectShape 6 4.25 4.2 3.0 0.75 "E8F2F8" "7EA4BD") + (TextBox 7 "Badge2" 4.55 4.38 2.4 0.4 @("97.92% Top-1 accuracy") 18 "24566B" $true) +
    (RectShape 8 7.7 4.2 3.9 0.75 "F6EBD8" "C6A56A") + (TextBox 9 "Badge3" 8.0 4.38 3.3 0.4 @("Live Gradio deployment") 18 "695026" $true) })

$teamShapes = (TextBox 2 "TeamTitle" 0.45 0.25 12.4 0.55 @("Team Members and Individual Contributions") 28 "114B3A" $true)
$xPositions = @(0.45, 3.05, 5.65, 8.25, 10.85)
$relLines = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $teamImages.Count; $i++) {
    $imgRel = 2 + $i
    $x = $xPositions[$i]
    $teamShapes += (RectShape (10+$i) $x 1.05 2.05 5.85 "FFFFFF" "CBDDD2")
    $teamShapes += (Picture (30+$i) $imgRel ($x+0.42) 1.22 1.2 1.2)
    $teamShapes += (TextBox (40+$i) ("Name"+$i) ($x+0.18) 2.62 1.7 0.42 @($teamImages[$i].Name) 15 "114B3A" $true)
    $teamShapes += (TextBox (50+$i) ("Role"+$i) ($x+0.18) 3.13 1.7 2.95 @($teamImages[$i].Role) 12 "263238" $false)
    $relLines.Add('<Relationship Id="rId' + $imgRel + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/team' + ($i+1) + '.jpg"/>')
}
$slides.Add(@{ Shapes = $teamShapes; Rels = $relLines.ToArray(); Copies = @($teamImages | ForEach-Object { $_.Path }) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Project Objectives") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.3 5.6 4.9 @("Problem", "- Manual food logging is slow and inconsistent.", "- Standard apps assume fixed 100 g portions.", "- Indian regional dishes are poorly covered.", "- Existing tools rarely estimate real food weight from an image.") 21 "263238" $false) +
    (TextBox 4 "Body2" 7.0 1.3 5.5 4.9 @("Objective", "- Upload one meal photo with a Rs. 10 coin.", "- Detect visible food regions automatically.", "- Classify the dish across 79 Indian categories.", "- Estimate portion weight and scale nutrition.", "- Present results clearly for everyday users.") 21 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Final Solution Overview") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.25 11.7 4.9 @("NutriVision is an end-to-end AI web application for Indian meal analysis.", "", "The user uploads a food photo, the backend analyzes the image, and the app returns an annotated result with food names, estimated grams, calories, and macro/micronutrients.", "", "The system combines computer vision, geometric calibration, food-specific density values, and a curated nutrition database so the result is more realistic than a fixed 100 g lookup.") 23 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Methodology") 30 "114B3A" $true) +
    (RectShape 3 0.75 1.25 2.2 3.9 "E8F2F8" "7EA4BD") + (TextBox 4 "M1" 0.95 1.55 1.8 3.0 @("Data", "Khana dataset, custom coin images, nutrition and density JSONs") 18 "24566B" $true) +
    (RectShape 5 3.2 1.25 2.2 3.9 "DDEFE6" "7BAE92") + (TextBox 6 "M2" 3.4 1.55 1.8 3.0 @("Vision", "SAM3 pixel masks plus ConvNeXtV2 Indian food classifier") 18 "114B3A" $true) +
    (RectShape 7 5.65 1.25 2.2 3.9 "F6EBD8" "C6A56A") + (TextBox 8 "M3" 5.85 1.55 1.8 3.0 @("Scale", "Rs. 10 coin detection converts pixels to real-world dimensions") 18 "695026" $true) +
    (RectShape 9 8.1 1.25 2.2 3.9 "F4E2E5" "BD8790") + (TextBox 10 "M4" 8.3 1.55 1.8 3.0 @("Weight", "PCA geometry and density-enforced LLM reasoning estimate grams") 18 "6E303A" $true) +
    (RectShape 11 10.55 1.25 2.2 3.9 "EEF0F2" "AAB2B8") + (TextBox 12 "M5" 10.75 1.55 1.8 3.0 @("Nutrition", "Per-100 g values are scaled to the estimated portion") 18 "263238" $true) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Final Backend Pipeline") 30 "114B3A" $true) +
    (TextBox 3 "Pipe" 0.85 1.3 11.7 4.9 @("Input food image", "-> SAM3 segmentation: masks for food, container, and coin", "-> Coin scale extraction: Rs. 10 coin maps pixels to centimeters", "-> ConvNeXtV2 classification: 79 supported dishes", "-> PCA geometry: major/minor axes for real-world size", "-> LLM weight estimation: geometry with hard density lookup", "-> Nutrition scaling: 11 nutrients from local database", "-> Output: annotated image, nutrition table, and reasoning") 22 "263238" $false) +
    (TextBox 4 "Note" 0.85 6.35 11.5 0.4 @("The presentation keeps the full pipeline to this slide so the final pipeline is not repeated unnecessarily.") 14 "51605A" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("What Happens During Backend Image Analysis") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.25 5.6 5.2 @("For technical audiences", "- Gradio streams progress after each backend stage.", "- Large uploads are resized before SAM3 to reduce GPU memory risk.", "- Coin detection is a required gate for scale calibration.", "- Low-confidence classification returns a clear failure message instead of misleading nutrition.") 20 "263238" $false) +
    (TextBox 4 "Body2" 7.0 1.25 5.5 5.2 @("For non-technical audiences", "- The app shows where it is in the analysis.", "- The coin acts like a ruler in the photo.", "- The final image labels food with estimated weight.", "- The nutrition table converts the image result into useful dietary information.") 20 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Dataset, Models, and Training") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.2 11.7 5.3 @("- Final food dataset: Khana source plus custom project additions.", "- Custom coin dataset supports scale and weight-estimation experiments.", "- ConvNeXtV2-Tiny became the top production classifier.", "- EfficientNetV2-S was evaluated as a strong comparison baseline.", "- Local nutrition database covers 79 Indian foods with 11 nutrients.", "- Food density database provides dish-specific g/cm3 values for realistic weight scaling.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Results and Performance") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.25 5.8 4.9 @("Classification results", "EfficientNetV2-S: 92.85% Top-1, F1 0.90", "ConvNeXtV2-Tiny: 97.92% Top-1, F1 0.97", "Top-5 accuracy: 99.76%", "", "Supported coverage", "79 Indian food categories with macro and micronutrient outputs.") 22 "263238" $false) +
    (TextBox 4 "Body2" 7.0 1.25 5.5 4.9 @("Real-world observations", "- Best on visually distinctive foods such as steamed momo, sabudana vada, sandwiches, and many curries.", "- Harder cases include visually similar pizza classes and low-quality photos.", "- Weight estimates are approximate, but more useful than fixed serving assumptions.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Web Application") 30 "114B3A" $true) +
    (Picture 3 2 0.75 1.15 5.65 4.4) + (Picture 4 3 6.9 1.15 5.65 4.4) +
    (TextBox 5 "Caption" 0.85 5.78 11.6 0.7 @("The deployed Gradio interface accepts meal images, streams backend progress, and returns an annotated image with nutrition results.") 18 "263238" $false);
    Rels = @('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/app_input.jpg"/>','<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/app_output.jpg"/>');
    Copies = @($appImage, $outputImage) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Live Web App Link") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.25 11.6 5.2 @("Show this slide before explaining the User Guide and Non-Technical Report.", "", "Primary deployment:", "https://7860-01kp8gvr84ng3myeemyw7vzz46.cloudspaces.litng.ai", "", "Mirror deployment:", "https://7860-01knjbx5j5gnvmttvxykcmx4bh.cloudspaces.litng.ai/", "", "Both links serve the same Gradio application running on Lightning AI with GPU acceleration.") 23 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Final Deliverables") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.85 1.25 5.6 5.2 @("User Guide", "- Explains how to run and use the app.", "- Covers image upload requirements.", "- Tells users to place a visible Rs. 10 coin.", "- Helps non-technical users understand outputs and errors.") 22 "263238" $false) +
    (TextBox 4 "Body2" 7.0 1.25 5.4 5.2 @("Non-Technical Report", "- Explains the problem, solution, evolution, results, limitations, and future work.", "- Uses plain language for evaluators and stakeholders.", "- Includes the repository link and final project summary.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Process and Project Stages") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.2 11.6 5.4 @("Milestone 1-2: Problem framing, dataset exploration, and nutrition mapping.", "Milestone 3: EDA, graphs, model experiments, and early evaluation.", "Milestone 4-5: Shift from YOLO/regression approach to stronger segmentation, classification, and geometry-based weight estimation.", "Milestone 6: Final reports, user/developer documentation, deployment, README, and updated presentation.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Limitations and Safeguards") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.25 11.6 5.2 @("- A Rs. 10 coin is required for scale; without it, the system stops before weight estimation.", "- The classifier supports 79 known classes; unknown foods are outside the current scope.", "- Similar-looking dishes can still be confused, especially pizza variants.", "- Weight estimates are approximations, not replacements for a kitchen scale.", "- Lighting, blur, occlusion, and extreme angles affect the final result.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Key Takeaways and Next Steps") 30 "114B3A" $true) +
    (TextBox 3 "Body" 0.8 1.2 11.6 5.4 @("Key takeaways", "- NutriVision turns one food image into practical nutrition information.", "- The final model reaches near-98% Top-1 food recognition across Indian dishes.", "- Coin calibration makes image-based weight estimation understandable and practical.", "", "Next steps", "- Expand the database beyond 150 Indian foods.", "- Improve performance on visually similar classes.", "- Explore mobile deployment and faster inference.", "- Add daily meal tracking and personalized nutrition recommendations.") 22 "263238" $false) })

$slides.Add(@{ Shapes = (TextBox 2 "Title" 0.65 0.35 12.0 0.6 @("Thank You") 34 "114B3A" $true) +
    (TextBox 3 "Body" 0.85 1.05 11.6 0.6 @("Final Milestone 6 submission image") 20 "263238" $false) +
    (Picture 4 2 2.5 1.85 8.3 4.6);
    Rels = @('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/final_image.jpg"/>');
    Copies = @($signImage) })

$contentTypes = @(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
    '<Default Extension="xml" ContentType="application/xml"/>',
    '<Default Extension="jpg" ContentType="image/jpeg"/>',
    '<Default Extension="jpeg" ContentType="image/jpeg"/>',
    '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
    '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
    '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
    '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
)
for ($i = 1; $i -le $slides.Count; $i++) {
    $contentTypes += '<Override PartName="/ppt/slides/slide' + $i + '.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
}
$contentTypes += '</Types>'
Add-Part "[Content_Types].xml" ($contentTypes -join "")

Add-Part "_rels/.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>'

$slideIds = ""
$presentationRels = '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
for ($i = 1; $i -le $slides.Count; $i++) {
    $rid = $i + 2
    $slideId = 255 + $i
    $slideIds += '<p:sldId id="' + $slideId + '" r:id="rId' + $rid + '"/>'
    $presentationRels += '<Relationship Id="rId' + $rid + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide' + $i + '.xml"/>'
}

Add-Part "ppt/presentation.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>$slideIds</p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>
"@

Add-Part "ppt/_rels/presentation.xml.rels" ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + $presentationRels + '</Relationships>')

Add-Part "ppt/theme/theme1.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="NutriVision"><a:themeElements><a:clrScheme name="NutriVision"><a:dk1><a:srgbClr val="263238"/></a:dk1><a:lt1><a:srgbClr val="F7FAF8"/></a:lt1><a:dk2><a:srgbClr val="114B3A"/></a:dk2><a:lt2><a:srgbClr val="FFFFFF"/></a:lt2><a:accent1><a:srgbClr val="2E7D5B"/></a:accent1><a:accent2><a:srgbClr val="24566B"/></a:accent2><a:accent3><a:srgbClr val="C6A56A"/></a:accent3><a:accent4><a:srgbClr val="BD8790"/></a:accent4><a:accent5><a:srgbClr val="7BAE92"/></a:accent5><a:accent6><a:srgbClr val="AAB2B8"/></a:accent6><a:hlink><a:srgbClr val="24566B"/></a:hlink><a:folHlink><a:srgbClr val="6E303A"/></a:folHlink></a:clrScheme><a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="NutriVision"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>
"@

Add-Part "ppt/slideMasters/slideMaster1.xml" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'
Add-Part "ppt/slideMasters/_rels/slideMaster1.xml.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'
Add-Part "ppt/slideLayouts/slideLayout1.xml" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
Add-Part "ppt/slideLayouts/_rels/slideLayout1.xml.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>'

$mediaCounter = 1
for ($i = 1; $i -le $slides.Count; $i++) {
    Add-Part ("ppt/slides/slide$i.xml") (SlideXml $slides[$i-1].Shapes)
    $rels = @()
    if ($slides[$i-1].ContainsKey("Rels")) {
        $rels = $slides[$i-1].Rels
        if ($slides[$i-1].ContainsKey("Copies")) {
            $copies = $slides[$i-1].Copies
            for ($j = 0; $j -lt $copies.Count; $j++) {
                if ($i -eq 2) { Copy-Part $copies[$j] ("ppt/media/team" + ($j+1) + ".jpg") }
                elseif ($i -eq 10 -and $j -eq 0) { Copy-Part $copies[$j] "ppt/media/app_input.jpg" }
                elseif ($i -eq 10 -and $j -eq 1) { Copy-Part $copies[$j] "ppt/media/app_output.jpg" }
                elseif ($i -eq $slides.Count) { Copy-Part $copies[$j] "ppt/media/final_image.jpg" }
                else { Copy-Part $copies[$j] ("ppt/media/image" + $mediaCounter + ".jpg"); $mediaCounter++ }
            }
        }
    }
    Add-Part ("ppt/slides/_rels/slide$i.xml.rels") (SlideRels $rels)
}

if (Test-Path $outPptx) { Remove-Item -LiteralPath $outPptx -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression
$archive = [System.IO.Compression.ZipFile]::Open($outPptx, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem -LiteralPath $tmp -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($tmp.Length + 1).Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $relative) | Out-Null
    }
}
finally {
    $archive.Dispose()
}
Remove-Item -LiteralPath $tmp -Recurse -Force
Write-Host "Created $outPptx"
