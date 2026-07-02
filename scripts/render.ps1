param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ArgsFromUser
)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
  & py "$ScriptDir\mono_diagram.py" render @ArgsFromUser
} else {
  & python "$ScriptDir\mono_diagram.py" render @ArgsFromUser
}
exit $LASTEXITCODE
