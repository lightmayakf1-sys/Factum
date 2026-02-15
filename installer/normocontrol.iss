; =============================================================================
; Normocontrol — Inno Setup Installer Script
; Версия: 2.0
; =============================================================================
;
; Требования для сборки:
;   1. Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;   2. Открыть этот файл в Inno Setup Compiler
;   3. Menu -> Build -> Compile (Ctrl+F9)
;   4. Готовый инсталлятор: installer\Output\Normocontrol_Setup.exe
;
; Предусловие для работы приложения:
;   Python 3.14 установлен в C:\Python314\
; =============================================================================

#define MyAppName "Normocontrol"
#define MyAppVersion "2.0"
#define MyAppPublisher "Normocontrol"
#define MyAppURL ""
#define MyAppExeName "Normocontrol.bat"
; Корень проекта — на одну папку выше от installer\
#define ProjectRoot ".."

[Setup]
; Уникальный ID приложения (НЕ менять после первого релиза!)
AppId={{B7E3F2A1-5C4D-4E6F-8A9B-1D2E3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE.txt
; Выходная папка и имя файла инсталлятора
OutputDir=Output
OutputBaseFilename=Normocontrol_Setup_{#MyAppVersion}
; Сжатие
Compression=lzma2/ultra64
SolidCompression=yes
; Иконка инсталлятора
SetupIconFile={#ProjectRoot}\normocontrol.ico
; Минимальная версия Windows
MinVersion=10.0
; Архитектура
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Разрешить выбор папки установки
DisableDirPage=no
; Разрешить выбор группы в меню Пуск
DisableProgramGroupPage=no
; Показать страницу «Готово» с галочкой запуска
DisableFinishedPage=no
; Права: обычный пользователь (не требует админа для установки самих файлов)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Информация для «Установка и удаление программ»
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\normocontrol.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на &Рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked
Name: "installdeps"; Description: "Установить Python-библиотеки после установки (требует Python 3.14)"; GroupDescription: "Настройка:"

[Files]
; === Главные файлы ===
Source: "{#ProjectRoot}\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\run_console.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\run.pyw"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\worker.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; === Лаунчер (.bat) ===
Source: "{#ProjectRoot}\Normocontrol.bat"; DestDir: "{app}"; Flags: ignoreversion

; === Установщик зависимостей ===
Source: "install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion

; === Модули Python (рекурсивно) ===
Source: "{#ProjectRoot}\scanner\*.py"; DestDir: "{app}\scanner"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\chunking\*.py"; DestDir: "{app}\chunking"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\gemini\*.py"; DestDir: "{app}\gemini"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\processing\*.py"; DestDir: "{app}\processing"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\output\*.py"; DestDir: "{app}\output"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}\gui\*.py"; DestDir: "{app}\gui"; Flags: ignoreversion recursesubdirs createallsubdirs

; === Иконка ===
Source: "{#ProjectRoot}\normocontrol.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Ярлык в меню Пуск — запуск через .bat
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\normocontrol.ico"; Comment: "Анализ паспортов оборудования"
; Ярлык на Рабочем столе (опционально)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\normocontrol.ico"; Comment: "Анализ паспортов оборудования"; Tasks: desktopicon
; Ярлык установки зависимостей в меню Пуск
Name: "{group}\Установить библиотеки"; Filename: "{app}\install_deps.bat"; WorkingDir: "{app}"; Comment: "Установка/обновление Python-библиотек"
; Ярлык деинсталляции в меню Пуск
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Пост-установка: установить Python-библиотеки (если выбрано)
Filename: "{app}\install_deps.bat"; Description: "Установка Python-библиотек..."; Tasks: installdeps; Flags: runascurrentuser waituntilterminated postinstall; StatusMsg: "Устанавливаю Python-библиотеки..."
; Запуск приложения после установки (галочка на финальной странице)
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent shellexec; WorkingDir: "{app}"

[UninstallDelete]
; Удалить __pycache__ при деинсталляции
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\scanner\__pycache__"
Type: filesandordirs; Name: "{app}\chunking\__pycache__"
Type: filesandordirs; Name: "{app}\gemini\__pycache__"
Type: filesandordirs; Name: "{app}\processing\__pycache__"
Type: filesandordirs; Name: "{app}\output\__pycache__"
Type: filesandordirs; Name: "{app}\gui\__pycache__"
; Удалить error_log если был создан
Type: files; Name: "{app}\error_log.txt"

[Code]
// Проверка наличия Python при установке
function IsPythonInstalled: Boolean;
begin
  Result := FileExists('C:\Python314\python.exe');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsPythonInstalled then
  begin
    if MsgBox(
      'Python 3.14 не найден в C:\Python314\' + #13#10 + #13#10 +
      'Для работы Normocontrol необходим Python 3.14.' + #13#10 +
      'Скачайте его с https://www.python.org/downloads/' + #13#10 +
      'и установите в папку C:\Python314\' + #13#10 + #13#10 +
      'Продолжить установку Normocontrol без Python?' + #13#10 +
      '(библиотеки можно будет установить позже)',
      mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;
