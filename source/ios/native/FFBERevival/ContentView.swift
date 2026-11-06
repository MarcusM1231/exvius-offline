import SwiftUI

struct ContentView: View {
    @AppStorage("backendAddress") private var address = "http://127.0.0.1:8765"
    @AppStorage("summonBackendMode") private var mode = "offline"
    @State private var pythonProof = "Not run yet"
    @StateObject private var model = SummonModel()

    var body: some View {
        TabView {
            NavigationStack {
                List {
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
                }.navigationTitle("FFBE Revival")
            }.tabItem { Label("Summon", systemImage: "sparkles") }
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
        }
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
    private func summon(_ banner: Banner, offer: Offer) async {
        do { await model.summon(banner, offer: offer, using: try backend(), identity: identity) }
        catch { model.error = error.localizedDescription }
    }
}
