; glb2stl Windows installer - Inno Setup 6
; Build (from the repository root, after PyInstaller):
;   iscc /DAppVersion=2.2.0 installer\glb2stl.iss
; Output: dist\glb2stl-v<version>-windows-setup.exe

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "glb2stl"
#define AppExe "glb2stl.exe"
#define AppURL "https://github.com/renero82/glb2stl"

[Setup]
AppId={{8F3C2A51-6D4B-4E8A-9C1F-2B7D5E9A4C3E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=renero82
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; per-user install by default (no admin rights needed), all-users on request
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}
OutputDir=..\dist
OutputBaseFilename=glb2stl-v{#AppVersion}-windows-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[CustomMessages]
english.AssocGroup=File associations:
english.AssocTask=Add glb2stl to "Open with" for .glb and .gltf files
italian.AssocGroup=Associazioni file:
italian.AssocTask=Aggiungi glb2stl ad "Apri con" per i file .glb e .gltf

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "assoc"; Description: "{cm:AssocTask}"; GroupDescription: "{cm:AssocGroup}"

[Files]
Source: "..\dist\glb2stl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; "Open with" entry for .glb/.gltf without taking over the user's default app
Root: HKA; Subkey: "Software\Classes\glb2stl.model"; ValueType: string; ValueName: ""; ValueData: "3D model (glTF)"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\glb2stl.model\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\glb2stl.model\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.glb\OpenWithProgids"; ValueType: string; ValueName: "glb2stl.model"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.gltf\OpenWithProgids"; ValueType: string; ValueName: "glb2stl.model"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
