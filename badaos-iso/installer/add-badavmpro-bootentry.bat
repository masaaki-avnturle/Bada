@echo off
rem ==========================================================================
rem  add-badavmpro-bootentry.bat  -  Windows の起動マネージャに
rem  「Bada VM Pro」を追加します (管理者として実行)。
rem  Bada VM Pro のブートローダは Windows の起動パーティション (ESP) の
rem  \EFI\BadaVMPro\ に置かれています。UEFI の起動メニューに出ない
rem  ファームウェアでも、これで Windows 側から Bada VM Pro を選べます。
rem ==========================================================================
setlocal
set LOADER=\EFI\BadaVMPro\shimx64.efi
mountvol S: /S >nul 2>&1
if not exist S:\EFI\BadaVMPro\shimx64.efi set LOADER=\EFI\BadaVMPro\grubx64.efi
mountvol S: /D >nul 2>&1
for /f "tokens=2 delims={}" %%G in ('bcdedit /copy {bootmgr} /d "Bada VM Pro"') do set GUID={%%G}
if "%GUID%"=="" (echo bcdedit に失敗しました。管理者として実行してください。& exit /b 1)
bcdedit /set %GUID% path %LOADER%
bcdedit /set {fwbootmgr} displayorder %GUID% /addfirst
echo Bada VM Pro を UEFI 起動順の先頭に追加しました: %GUID% (%LOADER%)
endlocal
