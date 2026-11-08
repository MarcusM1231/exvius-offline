import SwiftUI

// Receives a frontend receipt only. No backend reference or transaction callback.
struct SummonCrystalPresentation: View {
    let receipt: CommittedSummon
    let appearance: CrystalAppearance
    let complete: ([Award]) -> Void
    let fallback: ([Award]) -> Void
    @StateObject private var renderer: CrystalReconstructionController
    @State private var gate: SummonRevealGate
    @Environment(\.scenePhase) private var scenePhase
    init(receipt: CommittedSummon, appearance: CrystalAppearance, controller: CrystalReconstructionController? = nil, fallback: (([Award]) -> Void)? = nil, complete: @escaping ([Award]) -> Void) {
        self.receipt = receipt; self.appearance = appearance; self.complete = complete; self.fallback = fallback ?? complete
        _renderer = StateObject(wrappedValue: controller ?? CrystalReconstructionController())
        _gate = State(initialValue: SummonRevealGate(receipt: receipt))
    }
    var body: some View {
        ZStack(alignment: .topTrailing) {
            Color(red: 0.008,green: 0.018,blue: 0.045).ignoresSafeArea()
            VStack(spacing: 18) {
                Spacer(minLength: 15)
                ReconstructedCrystalViewport(controller: renderer)
                    .overlay(alignment: .bottom) { CrystalTouchPrompt(controller: renderer).padding(.bottom,14) }
                    .contentShape(Rectangle())
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel(renderer.tapPhase == .waitingForTap ? "TOUCH SCREEN" : "Summon crystal")
                    .accessibilityAddTraits(.isButton)
                    .accessibilityAction { renderer.tapToBreak() }
                    .accessibilityIdentifier("summon-crystal-area")
                Text(renderer.tapPhase == .arriving ? "An ally awaits…" : "")
                    .font(.headline).foregroundStyle(.white.opacity(0.8)).frame(height: 30)
                    .accessibilityIdentifier("tap-to-break-prompt")
            }.padding(.bottom,20).contentShape(Rectangle()).onTapGesture { renderer.tapToBreak() }
            Button("Skip") { finish(.skipped) }.font(.callout).foregroundStyle(.white.opacity(0.75)).padding(18)
                .accessibilityIdentifier("skip-summon-crystal")
        }.preferredColorScheme(.dark).interactiveDismissDisabled()
            .task {
                renderer.appearance = appearance
                renderer.onCompletion = { outcome in
                    switch outcome {
                    case .finished: finish(.opened)
                    case .cancelled: finish(.interrupted)
                    case .unavailable: finish(.unavailable)
                    }
                }
                renderer.load()
                guard renderer.ready else { finish(.unavailable); return }
                renderer.startTapPresentation()
                if scenePhase != .active { renderer.suspend() }
            }
            .onChange(of: scenePhase) { value in
                if value == .active { renderer.resumeTapPresentation() } else { renderer.suspend() }
            }
            .onDisappear { finish(.interrupted) }
    }
    private func finish(_ reason: SummonRevealReason) {
        guard let awards = gate.finish(reason: reason) else { return }
        renderer.onCompletion = nil; renderer.stop()
        if reason == .opened { complete(awards) } else { fallback(awards) }
    }
}
