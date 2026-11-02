function ConvertTo-QemuArgument {
    param([string]$Value)

    if ($Value -and $Value -notmatch '[ \t"]') { return $Value }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append('\' * (2 * $backslashes + 1))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes) {
            [void]$builder.Append('\' * $backslashes)
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes) {
        [void]$builder.Append('\' * (2 * $backslashes))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Join-QemuArguments {
    param([string[]]$Arguments)

    return (@($Arguments | ForEach-Object { ConvertTo-QemuArgument $_ }) -join ' ')
}
