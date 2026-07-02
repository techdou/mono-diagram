param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ArgsFromUser
)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
  & py "$ScriptDir\mono_diagram.py" validate @ArgsFromUser
} else {
  & python "$ScriptDir\mono_diagram.py" validate @ArgsFromUser
}
exit $LASTEXITCODE
