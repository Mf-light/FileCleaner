; FileCleaner NSIS install script
; Supports custom install path + optional desktop shortcut (default checked)

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ===== Basic Info =====
Name "FileCleaner"
OutFile "dist\FileCleaner_Setup.exe"
InstallDir "$PROGRAMFILES64\FileCleaner"
InstallDirRegKey HKCU "Software\FileCleaner" ""
RequestExecutionLevel admin

; ===== Version Info =====
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "FileCleaner"
VIAddVersionKey "CompanyName" "FileCleaner"
VIAddVersionKey "LegalCopyright" "(C) 2025"
VIAddVersionKey "FileDescription" "File Cleaner - Auto clean expired files"
VIAddVersionKey "FileVersion" "1.0.0.0"

; ===== MUI Settings =====
!define MUI_ABORTWARNING
!define MUI_ICON "resources\app.ico"
!define MUI_UNICON "resources\app.ico"

; ----- Welcome -----
!insertmacro MUI_PAGE_WELCOME

; ----- Select Install Directory -----
!insertmacro MUI_PAGE_DIRECTORY

; ----- Components -----
!define MUI_COMPONENTSPAGE_TEXT_TOP "Select components to install:"
!define MUI_COMPONENTSPAGE_TEXT_COMPLIST "Check the components you want to install:"
Var CREATE_DESKTOP_SHORTCUT
!insertmacro MUI_PAGE_COMPONENTS

; ----- Install Progress -----
!insertmacro MUI_PAGE_INSTFILES

; ----- Finish -----
!define MUI_FINISHPAGE_RUN "$INSTDIR\FileCleaner.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Run FileCleaner"
!insertmacro MUI_PAGE_FINISH

; ----- Uninstall -----
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ===== Languages =====
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ===== Component Definitions =====
Section "Main Program (Required)" SectionMain
    SectionIn RO

    SetOutPath "$INSTDIR"

    ; Copy all PyInstaller onedir files
    File /r "dist\FileCleaner\*.*"

    ; Register uninstall info
    WriteRegStr HKCU "Software\FileCleaner" "" $INSTDIR
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add to Add/Remove Programs
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner" \
                     "DisplayName" "FileCleaner"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner" \
                     "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner" \
                     "DisplayIcon" '$INSTDIR\FileCleaner.exe,0'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner" \
                     "Publisher" "FileCleaner"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner" \
                     "InstallLocation" "$INSTDIR"
SectionEnd

Section /o "Create Desktop Shortcut" SectionDesktop
    CreateShortCut "$DESKTOP\FileCleaner.lnk" "$INSTDIR\FileCleaner.exe" "" \
                   "$INSTDIR\FileCleaner.exe" 0
SectionEnd

; ===== Descriptions =====
LangString DESC_SectionMain ${LANG_SIMPCHINESE} "主程序文件"
LangString DESC_SectionDesktop ${LANG_SIMPCHINESE} "创建桌面快捷方式"
LangString DESC_SectionMain ${LANG_ENGLISH} "Main program files"
LangString DESC_SectionDesktop ${LANG_ENGLISH} "Create desktop shortcut"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SectionMain} $(DESC_SectionMain)
    !insertmacro MUI_DESCRIPTION_TEXT ${SectionDesktop} $(DESC_SectionDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ===== Uninstaller =====
Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\FileCleaner.lnk"
    DeleteRegKey HKCU "Software\FileCleaner"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FileCleaner"
SectionEnd
