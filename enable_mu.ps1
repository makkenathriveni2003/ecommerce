try {
    $serviceManager = New-Object -ComObject "Microsoft.Update.ServiceManager"
    $serviceManager.ClientApplicationID = "WSLUpdateHelper"
    $service = $serviceManager.AddService2("7971f918-a847-4430-9279-4a52d1efe18d", 7, "")
    Write-Host "Successfully enabled Microsoft Update! Service Name: " $service.Name
} catch {
    Write-Host "Error enabling Microsoft Update: " $_.Exception.Message
}
