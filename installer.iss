; Inno Setup script — Prompt Sessie Manager
; Compileren met Inno Setup 6+: https://jrsoftware.org/isinfo.php
; Resultaat: een installeerbaar .exe-bestand

[Setup]
AppName=Prompt Sessie Manager
AppVersion=1.0
AppPublisher=Jouw Naam
DefaultDirName={localappdata}\PromptSessieManager
DefaultGroupName=Prompt Sessie Manager
OutputBaseFilename=PromptSessieManager-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Geen beheerdersrechten nodig — installeert per gebruiker
PrivilegesRequired=lowest

[Languages]
Name: "nl"; MessagesFile: "compiler:Languages\Dutch.isl"

[Files]
; Alle projectbestanden meepakken
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs
; Het installerscript zelf meepakken (voor herinstallatie)
Source: "installeer.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Lege mappen aanmaken
Name: "{app}\sessions"
Name: "{app}\outputs"
Name: "{app}\logs"

[Icons]
; Snelkoppeling op bureaublad
Name: "{userdesktop}\Prompt Sessie Manager"; Filename: "{app}\start.bat"; \
  Comment: "Start de Prompt Sessie Manager"
; Snelkoppeling in Startmenu
Name: "{group}\Prompt Sessie Manager"; Filename: "{app}\start.bat"
Name: "{group}\Verwijderen"; Filename: "{uninstallexe}"

[Run]
; Na installatie: installeer-script uitvoeren (Python + Ollama + pip)
Filename: "{app}\installeer.bat"; \
  Description: "Python, Ollama en het AI-model installeren"; \
  Flags: postinstall runascurrentuser; \
  StatusMsg: "Benodigde software installeren..."

[UninstallDelete]
; Bij verwijderen ook de gecreëerde mappen opruimen
Type: filesandordirs; Name: "{app}\sessions"
Type: filesandordirs; Name: "{app}\outputs"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
