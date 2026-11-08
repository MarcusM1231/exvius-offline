import SwiftUI

struct ContentView: View {
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage("backendAddress") private var address = "http://127.0.0.1:8765"
    @AppStorage("summonBackendMode") private var mode = "offline"
    @State private var confirmsLapisGrant = false
    @State private var pythonProof = "Not run yet"
    @StateObject private var model = SummonModel()

    var body: some View {
        TabView {
            GlobalSummonScreen(model: model, refresh: { await refresh() }) { banner, offer in
                await summon(banner, offer: offer)
            }.id(identity).tabItem { Label("Summon", systemImage: "sparkles") }
            NavigationStack {
                List(model.campaign?.units ?? []) { unit in
                    UnitRowView(unit: UnitCatalog.display(masterID: unit.master_id, backendName: unit.name,
                                                          rarity: unit.granted_rarity, isAward: false),
                                inventoryDetail: "Level \(unit.level) · Copy #\(unit.instance_id)")
                }
                .overlay {
                    if model.campaign == nil { Text("Refresh to load your collection.").foregroundStyle(.secondary) }
                }
                .navigationTitle("Collection (\(model.campaign?.units.count ?? 0))")
            }.tabItem { Label("Collection", systemImage: "person.3") }
            NavigationStack {
                List {
                    Section("Character reveal research") {
                        NavigationLink("Original unit animations") { UnitAnimationGallery() }
                        NavigationLink("Inspect reveal artwork candidates") { RevealResearchPreview() }
                    }
                    Section("Crystal recovery") {
                        NavigationLink("Inspect original crystal mesh") { CrystalPreview() }
                        Text("Isolated diagnostic preview; no summon or currency cost.").font(.caption)
                    }
                    Section("Embedded Python proof") {
                        Text(pythonProof).font(.caption)
                        Button("Run Python on this device") {
                            Task {
                                do {
                                    let proof: PythonProof = try await PythonWorker.shared.call(["operation": "hello"])
                                    pythonProof = "\(proof.message) · \(proof.platform) · 6 × 7 = \(proof.answer) · \(proof.version)"
                                } catch { pythonProof = error.localizedDescription }
                            }
                        }
                    }
                    Section("Personal campaign tools") {
                        Button("Add 10,000 free Lapis…") { confirmsLapisGrant = true }
                            .disabled(mode != "offline" || model.busy || model.needsRefresh)
                        Text("Explicitly adds free Lapis to this device’s current campaign and saves it. Available in offline mode only.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Section("Backend") {
                        Picker("Mode", selection: $mode) {
                            Text("On-device Python").tag("offline")
                            Text("HTTP development").tag("http")
                        }.disabled(model.busy)
                        if mode == "http" {
                            TextField("http://Mac-LAN-IP:8765", text: $address)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.URL)
                                .disabled(model.busy)
                            Text("HTTP uses a separate campaign on your Mac.")
                                .font(.caption).foregroundStyle(.secondary)
                        } else {
                            Text("Campaign saved on this device. Wi-Fi and the Mac are not required.")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Button("Refresh saved state") { Task { await refresh() } }
                            .disabled(model.busy)
                    }
                    if model.busy { ProgressView("Loading campaign…") }
                    if let error = model.error {
                        Section("Could not complete request") { Text(error).foregroundStyle(.red) }
                    }
                    if let state = model.campaign {
                        Section("Campaign") {
                            Text("Lapis: \((state.currencies["lapis_free"] ?? 0) + (state.currencies["lapis_paid"] ?? 0))")
                                .font(.headline)
                            ForEach(state.currencies.keys.sorted(), id: \.self) { key in
                                LabeledContent(key, value: String(state.currencies[key] ?? 0))
                            }
                            if state.demo_metadata {
                                Text(UnitCatalog.shared?.mode == "preservation"
                                     ? "Demo gameplay data · Global-targeted names · \(UnitCatalog.shared?.artworkCount ?? 0) artwork IDs"
                                     : "Demo metadata · placeholder units · real backend transactions")
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                    Section("Summon banners") {
                        ForEach(model.banners) { banner in
                            VStack(alignment: .leading, spacing: 10) {
                                Text(banner.name).font(.headline)
                                Text("Banner \(banner.id)").font(.caption).foregroundStyle(.secondary)
                                if banner.supported {
                                    ForEach(banner.offer_details) { offer in
                                        Button("Summon ×\(offer.draws) — \(offer.cost?.label ?? "Free")") {
                                            Task { await summon(banner, offer: offer) }
                                        }
                                        .buttonStyle(.borderedProminent)
                                        .disabled(model.busy || model.needsRefresh)
                                    }
                                } else {
                                    Text("This banner needs a future interface extension.").font(.caption)
                                }
                            }.padding(.vertical, 6)
                        }
                    }
                    Section("Latest saved summon") {
                        if model.results.isEmpty { Text("No summon results yet.").foregroundStyle(.secondary) }
                        ForEach(model.results) { award in
                            UnitRowView(unit: UnitCatalog.display(masterID: award.unit_id, backendName: award.name,
                                                                  rarity: award.granted_rarity, isAward: true),
                                        inventoryDetail: nil)
                        }
                    }
                }.navigationTitle("Developer Tools")
            }.tabItem { Label("Developer", systemImage: "wrench.and.screwdriver") }
        }
        .confirmationDialog("Add 10,000 free Lapis to this campaign?", isPresented: $confirmsLapisGrant, titleVisibility: .visible) {
            Button("Add and save 10,000 Lapis") {
                Task {
                    guard mode == "offline", !model.busy else { return }
                    model.busy = true
                    do { model.campaign = try await EmbeddedSummonBackend.shared.developerAddLapis(amount: 10000); model.error = nil }
                    catch { model.error = error.localizedDescription; model.needsRefresh = true }
                    model.busy = false
                }
            }
            Button("Cancel", role: .cancel) {}
        }
        .preferredColorScheme(.dark)
        .task {
            let arguments = ProcessInfo.processInfo.arguments
            if arguments.contains("--python-proof") {
                pythonProof = await PythonDiagnostics.proof()
            } else if arguments.contains("--offline-self-test") || arguments.contains("--offline-self-test-reload") {
                pythonProof = await PythonDiagnostics.offlineCheck(arguments: arguments)
            } else {
                pythonProof = await PythonDiagnostics.proof()
                await refresh()
            }
        }
        .onChange(of: scenePhase) { phase in
            if phase == .active && !ProcessInfo.processInfo.arguments.contains(where: { $0.hasPrefix("--offline-self-test") }) {
                Task { await refresh() }
            }
        }
        .onChange(of: address) { _ in model.addressChanged() }
        .onChange(of: mode) { _ in
            model.addressChanged()
            Task { await refresh() }
        }
    }

    private var identity: String { mode == "offline" ? "offline" : address }
    private func backend() throws -> any SummonBackend {
        mode == "offline" ? EmbeddedSummonBackend.shared : try HTTPBackend(address: address)
    }
    private func refresh() async {
        do { await model.refresh(using: try backend(), identity: identity) }
        catch { model.error = error.localizedDescription }
    }
    private func summon(_ banner: Banner, offer: Offer) async -> Bool {
        do { return await model.summon(banner, offer: offer, using: try backend(), identity: identity) }
        catch { model.error = error.localizedDescription; return false }
    }
}
