; 收藏学习台 Windows 安装包（Inno Setup 6）。不要直接编译，用 build_windows.ps1，它会先准备好 StageDir。
; 装在当前用户目录下，不需要管理员权限；升级时覆盖程序文件，data 文件夹（笔记、进度、设置）不动。

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef StageDir
  #error 请用 installer\build_windows.ps1 打包
#endif

[Setup]
AppId={{6F0B8E52-3C1D-4D8A-9E57-2B4C1A7D9F10}
AppName=收藏学习台
AppVersion={#AppVersion}
AppVerName=收藏学习台 {#AppVersion}
AppPublisher=yuanshengbo8-sketch
AppPublisherURL=https://github.com/yuanshengbo8-sketch/douyin-fav-study
AppSupportURL=https://github.com/yuanshengbo8-sketch/douyin-fav-study/issues
; 路径只用英文：部分语音识别组件在中文路径下会出错
DefaultDirName={localappdata}\Programs\DouyinFavStudy
DefaultGroupName=收藏学习台
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputBaseFilename=DouyinFavStudy-Setup-{#AppVersion}
SetupIconFile={#StageDir}\app.ico
UninstallDisplayIcon={app}\app.ico
UninstallDisplayName=收藏学习台
Compression=lzma2/max
SolidCompression=yes
; 编译器本身是 32 位的，压缩五百多 MB 会内存不够；放到单独的 64 位进程里压缩
LZMAUseSeparateProcess=yes
WizardStyle=modern
; 程序正在运行时，安装前先帮用户关掉（python.exe 会占用文件）
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no

[Languages]
#ifdef LangFile
Name: "chs"; MessagesFile: "{#LangFile}"
#else
Name: "en"; MessagesFile: "compiler:Default.isl"
#endif

[Tasks]
Name: "desktopicon"; Description: "在桌面创建快捷方式"; GroupDescription: "快捷方式："

[InstallDelete]
; 升级前清掉旧的程序文件，避免残留；data 不在这里，不会被删
Type: filesandordirs; Name: "{app}\app"
Type: filesandordirs; Name: "{app}\python"

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\收藏学习台"; Filename: "{app}\python\python.exe"; Parameters: "-X utf8 -m app"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Comment: "抖音收藏 → 学习笔记"
Name: "{autodesktop}\收藏学习台"; Filename: "{app}\python\python.exe"; Parameters: "-X utf8 -m app"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\python.exe"; Parameters: "-X utf8 -m app"; WorkingDir: "{app}"; Description: "现在打开收藏学习台"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; 运行时生成的缓存文件
Type: filesandordirs; Name: "{app}\app"
Type: filesandordirs; Name: "{app}\python"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  DataDir := ExpandConstant('{app}\data');
  if (CurUninstallStep = usPostUninstall) and DirExists(DataDir) then
    if SuppressibleMsgBox('要同时删除你的笔记、学习记录和设置吗？' + #13#10 + '（保存在 ' + DataDir + '）' + #13#10#13#10 +
        '选「否」会保留下来，重新安装后可以接着用。', mbConfirmation, MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES then
      DelTree(DataDir, True, True, True);
end;
