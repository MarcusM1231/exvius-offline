import SwiftUI

@main
struct FFBERevivalApp: App {
    var body: some Scene {
        WindowGroup {
            if ProcessInfo.processInfo.arguments.contains("--expanded-unit-art-check") {
                ExpandedArtDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--extra-unit-art-check") {
                ExtraUnitArtDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--banner-menu-test") {
                BannerMenuDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--banner-research-preview") {
                NavigationStack { BannerResearchPreview() }
            } else if ProcessInfo.processInfo.arguments.contains("--unit-attack-diagnostics") {
                UnitAttackDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--unit-action-diagnostics") {
                UnitActionDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--unit-action-preview") {
                NavigationStack { UnitActionResearchView() }
            } else if ProcessInfo.processInfo.arguments.contains("--unit-animation-gallery") {
                NavigationStack { UnitAnimationGallery() }
            } else if ProcessInfo.processInfo.arguments.contains("--unit-animation-diagnostics") {
                UnitAnimationDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--unit-animation-preview") {
                NavigationStack { UnitAnimationPreview() }
            } else if ProcessInfo.processInfo.arguments.contains("--falling-summon-diagnostics") || ProcessInfo.processInfo.arguments.contains("--character-reveal-diagnostics") || ProcessInfo.processInfo.arguments.contains("--character-reveal-reload-check") {
                CharacterRevealDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--character-reveal-lab") {
                TapSummonDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains(where: { ["--tap-summon-diagnostics","--tap-summon-reload-check","--tap-summon-lab"].contains($0) }) {
                TapSummonDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--falling-crystal-diagnostics") || ProcessInfo.processInfo.arguments.contains("--crystal-reconstruction") || ProcessInfo.processInfo.arguments.contains("--crystal-reconstruction-diagnostics") {
                NavigationStack { CrystalReconstructionPreview() }
            } else if ProcessInfo.processInfo.arguments.contains("--crystal-preview") || ProcessInfo.processInfo.arguments.contains("--crystal-diagnostics") {
                NavigationStack { CrystalPreview() }
            } else if ProcessInfo.processInfo.arguments.contains("--summon-ui-diagnostics") {
                SummonInterfaceDiagnostics()
            } else if ProcessInfo.processInfo.arguments.contains("--reveal-research-preview") {
                NavigationStack { RevealResearchPreview() }
            } else if ProcessInfo.processInfo.arguments.contains("--unit-artwork-preview") {
                UnitArtworkPreview()
            } else { ContentView() }
        }
    }
}
