$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'qemu-args.ps1')

$python = 'py'
$program = 'import sys, json; print(json.dumps(sys.argv[1:]))'

function Get-QemuArgv {
    param([string[]]$Arguments)

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $python
    $startInfo.Arguments = Join-QemuArguments (@('-c', $program) + $Arguments)
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($startInfo)
    try {
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        $exitCode = $process.ExitCode
    } finally {
        $process.Dispose()
    }
    if ($exitCode -ne 0) { throw "Python failed: $stderr" }
    $decoded = ConvertFrom-Json $stdout
    return @($decoded)
}

function Test-QemuArguments {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $expected = @($Arguments)
    $received = @(Get-QemuArgv $Arguments)
    if ($received.Count -ne $expected.Count) {
        Write-Host "FAIL: ${Name}: expected $($expected.Count) arguments, received $($received.Count)"
        exit 1
    }
    for ($index = 0; $index -lt $expected.Count; $index++) {
        if ($received[$index] -cne $expected[$index]) {
            Write-Host "FAIL: ${Name}: argument $index expected [$($expected[$index])], received [$($received[$index])]"
            exit 1
        }
    }
    Write-Host "PASS: $Name"
}

$kernelCommandLine = 'console=ttyAMA0,115200 root=/dev/vda rw quiet loglevel=0 stearlight.boot-epoch=1700000000'

Test-QemuArguments 'plain paths' @(
    '-L', 'F:/Stearlight/qemu/share',
    '-kernel', 'F:/Stearlight/out/vmlinuz-virt',
    '-append', $kernelCommandLine
)

Test-QemuArguments 'spaced output directory' @(
    '-L', 'F:/Stearlight Test/qemu/share',
    '-serial', 'file:F:/Stearlight Test/shared/serial-test.log',
    '-kernel', 'F:\Stearlight Test\out\vmlinuz',
    '-initrd', 'F:\Stearlight Test\out\initramfs',
    '-drive', 'file=F:/Stearlight Test/shared/stearlight-arm64.ext4,format=raw,if=virtio'
)

Test-QemuArguments 'kernel command line' @(
    '-append', 'console=ttyAMA0,115200 root=/dev/vda rootfstype=ext4 rw quiet stearlight.capture=1'
)

Test-QemuArguments 'embedded quote' @(
    '-append', 'console=ttyAMA0 stearlight.note="quoted value" root=/dev/vda'
)

Test-QemuArguments 'trailing backslash' @(
    '-kernel', 'C:\a b\'
)

Test-QemuArguments 'empty string' @(
    '-kernel', ''
)

$spacedDirectory = 'F:\Stearlight Test\out'
$plainDirectory = 'F:\Stearlight\out'
$spacedArguments = @(
    '-L', (Join-Path $spacedDirectory 'share'),
    '-serial', ('file:' + (Join-Path $spacedDirectory 'serial-test.log').Replace('\', '/')),
    '-kernel', (Join-Path $spacedDirectory 'vmlinuz-virt'),
    '-initrd', (Join-Path $spacedDirectory 'initramfs-virt'),
    '-append', $kernelCommandLine
)
$plainArguments = @(
    '-L', (Join-Path $plainDirectory 'share'),
    '-serial', ('file:' + (Join-Path $plainDirectory 'serial-test.log').Replace('\', '/')),
    '-kernel', (Join-Path $plainDirectory 'vmlinuz-virt'),
    '-initrd', (Join-Path $plainDirectory 'initramfs-virt'),
    '-append', $kernelCommandLine
)
$spacedArgv = @(Get-QemuArgv $spacedArguments)
$plainArgv = @(Get-QemuArgv $plainArguments)
if ($spacedArgv.Count -ne $plainArgv.Count) {
    Write-Host "FAIL: spaced comparison: argument counts differ ($($spacedArgv.Count) and $($plainArgv.Count))"
    exit 1
}
for ($index = 0; $index -lt $spacedArgv.Count; $index++) {
    $normalized = $spacedArgv[$index].Replace($spacedDirectory, $plainDirectory).Replace(
        $spacedDirectory.Replace('\', '/'), $plainDirectory.Replace('\', '/'))
    if ($normalized -cne $plainArgv[$index]) {
        Write-Host "FAIL: spaced comparison: argument $index expected [$($plainArgv[$index])], received [$($spacedArgv[$index])]"
        exit 1
    }
}
Write-Host 'PASS: spaced and unspaced output directories'

exit 0
