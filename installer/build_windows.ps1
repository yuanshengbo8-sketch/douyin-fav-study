<#
  打包 Windows 一键安装包：内置 Python 3.12 和全部组件，用户双击 setup.exe 就能用，不用自己装 Python。

  需要：Windows x64、能联网、Inno Setup 6（https://jrsoftware.org/isdl.php，免费）。
  用法（在仓库根目录）：
      powershell -ExecutionPolicy Bypass -File installer\build_windows.ps1
      powershell -ExecutionPolicy Bypass -File installer\build_windows.ps1 -PipIndex https://pypi.tuna.tsinghua.edu.cn/simple
  产物：dist\DouyinFavStudy-Setup-<版本>.exe
#>
param(
  [string]$PyVersion = "3.12.10",
  [string]$PipIndex = "",       # 国内网络慢时可以换成清华镜像
  [switch]$SkipCompile          # 只准备文件（build\windows\stage），不调用 Inno Setup
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest 不显示进度条会快很多
$Root = Split-Path -Parent $PSScriptRoot
$Build = Join-Path $Root "build\windows"
$Stage = Join-Path $Build "stage"
$Cache = Join-Path $Build "cache"
$Version = (Select-String -Path "$Root\app\__init__.py" -Pattern '__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
Write-Host "== 收藏学习台 v$Version 安装包 =="

New-Item -ItemType Directory -Force $Cache | Out-Null
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Force $Stage | Out-Null

function Get-File($url, $out) {
  if (-not (Test-Path $out)) {
    Write-Host "下载 $url"
    Invoke-WebRequest $url -OutFile "$out.part" -UseBasicParsing
    Move-Item "$out.part" $out
  }
}

# 1. 嵌入版 Python（官方 zip，约 10MB）
Write-Host "[1/4] 准备 Python $PyVersion"
$PyZip = Join-Path $Cache "python-$PyVersion-embed-amd64.zip"
Get-File "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-embed-amd64.zip" $PyZip
$Py = Join-Path $Stage "python"
Expand-Archive $PyZip $Py
# 嵌入版默认不读 site-packages，也找不到程序目录里的 app 包：改 ._pth 把它们加进来
$pth = Get-ChildItem $Py -Filter "python*._pth" | Select-Object -First 1
$stdlib = (Get-ChildItem $Py -Filter "python3*.zip" | Select-Object -First 1).Name
Set-Content $pth.FullName -Encoding ascii -Value @($stdlib, ".", "..", "Lib\site-packages", "import site")
# 有的组件（onnxruntime 等）要 VC++ 运行库；干净的系统上可能没装，放一份在 python.exe 旁边（微软允许这样随程序分发）
foreach ($dll in "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll", "vcruntime140_1.dll", "concrt140.dll") {
  $src = Join-Path "$env:WINDIR\System32" $dll
  if ((Test-Path $src) -and -not (Test-Path (Join-Path $Py $dll))) { Copy-Item $src $Py }
}
$PyExe = Join-Path $Py "python.exe"

# 2. pip 和组件
Write-Host "[2/4] 安装组件（playwright、faster-whisper、rapidocr，需要几分钟）"
$GetPip = Join-Path $Cache "get-pip.py"
Get-File "https://bootstrap.pypa.io/get-pip.py" $GetPip
$idx = @(); if ($PipIndex) { $idx = @("-i", $PipIndex) }
& $PyExe $GetPip --no-warn-script-location @idx
if ($LASTEXITCODE) { throw "pip 安装失败" }
& $PyExe -m pip install --no-warn-script-location --disable-pip-version-check -r "$Root\requirements.txt" @idx
if ($LASTEXITCODE) { throw "组件安装失败" }

# 3. 程序文件
Write-Host "[3/4] 复制程序文件"
Copy-Item "$Root\app" (Join-Path $Stage "app") -Recurse
Copy-Item "$Root\installer\app.ico", "$Root\LICENSE.md" $Stage
Get-ChildItem $Stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 检查：组件都能 import（不 import app.server，免得在打包目录里生成 data 文件夹）
Push-Location $Stage
try {
  & $PyExe -X utf8 -c "import app, playwright, faster_whisper, rapidocr_onnxruntime, ctranslate2, onnxruntime, av; print('组件检查通过 v' + app.__version__)"
  if ($LASTEXITCODE) { throw "组件检查没通过" }
} finally { Pop-Location }
Get-ChildItem $Stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
$size = (Get-ChildItem $Stage -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host ("    打包内容 {0:N0} MB" -f $size)
if ($SkipCompile) { Write-Host "已跳过编译，文件在 $Stage"; exit 0 }

# 4. 用 Inno Setup 编译成 setup.exe
Write-Host "[4/4] 编译安装包"
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { $iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source }
if (-not $iscc) { throw "没找到 Inno Setup 6。请先安装：https://jrsoftware.org/isdl.php（或 winget install JRSoftware.InnoSetup）" }
# 简体中文界面：新版 Inno Setup 自带就用自带的，否则从官方仓库固定版本里取一份
$Lang = Join-Path (Split-Path $iscc) "Languages\ChineseSimplified.isl"
if (-not (Test-Path $Lang)) {
  $Lang = Join-Path $Cache "ChineseSimplified.isl"
  Get-File "https://raw.githubusercontent.com/jrsoftware/issrc/is-6_7_3/Files/Languages/Unofficial/ChineseSimplified.isl" $Lang
}
& $iscc "/DAppVersion=$Version" "/DStageDir=$Stage" "/DLangFile=$Lang" "/O$Root\dist" "$Root\installer\setup.iss"
if ($LASTEXITCODE) { throw "Inno Setup 编译失败" }
Get-Item "$Root\dist\DouyinFavStudy-Setup-$Version.exe" | ForEach-Object { Write-Host ("完成：{0}（{1:N0} MB）" -f $_.FullName, ($_.Length / 1MB)) }
