@rem Minimal Gradle wrapper launcher (Windows) for the Bada CodeFix Android app.
@if "%DEBUG%"=="" @echo off
setlocal

set APP_HOME=%~dp0
set WRAPPER_JAR=%APP_HOME%gradle\wrapper\gradle-wrapper.jar

if defined JAVA_HOME (
    set JAVACMD=%JAVA_HOME%\bin\java.exe
) else (
    set JAVACMD=java.exe
)

"%JAVACMD%" %JAVA_OPTS% %GRADLE_OPTS% -classpath "%WRAPPER_JAR%" org.gradle.wrapper.GradleWrapperMain %*

endlocal
