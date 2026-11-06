import SwiftUI

@main
struct FFBERevivalApp: App {
    var body: some Scene {
        WindowGroup {
            if ProcessInfo.processInfo.arguments.contains("--summon-ui-diagnostics") {
                SummonInterfaceDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--unit-artwork-preview") {
                UnitArtworkPreview()
            } else { ContentView() }
        }
    }
}
