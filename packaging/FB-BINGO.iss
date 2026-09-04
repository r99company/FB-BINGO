#define AppName "FB-BINGO"
#define AppVersion "0.1.0"
#define AppPublisher "FB-BINGO"
#define AppExeName "FB-BINGO.exe"

[Setup]
AppId={{A5F8C1F5-9A6C-4A65-BB1D-7F9E5F7B8D90}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\FB-BINGO
DefaultGroupName=FB-BINGO
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=FB-BINGO-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayName=FB-BINGO

[Files]
Source: "..\dist\FB-BINGO\FB-BINGO.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FB-BINGO"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\FB-BINGO"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar FB-BINGO"; Flags: nowait postinstall skipifsilent
