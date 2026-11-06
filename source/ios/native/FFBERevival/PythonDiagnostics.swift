import Foundation

@MainActor
enum PythonDiagnostics {
    static func proof() async -> String {
        do {
            let proof: PythonProof = try await PythonWorker.shared.call(["operation": "hello"])
            let folder = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                     appropriateFor: nil, create: true)
                .appendingPathComponent("FFBERevival/validation", isDirectory: true)
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            let result: [String: Any] = ["message": proof.message, "platform": proof.platform,
                                        "version": proof.version, "answer": proof.answer]
            try JSONSerialization.data(withJSONObject: result, options: .sortedKeys)
                .write(to: folder.appendingPathComponent("python-proof.json"), options: .atomic)
            let message = "\(proof.message) · \(proof.platform) · 6 × 7 = \(proof.answer) · \(proof.version)"
            print(message)
            return message
        } catch { return error.localizedDescription }
    }

    private struct Diagnostics: Decodable {
        let network_rejected: Bool
        let save: String
        let metadata: String
        let platform: String
    }

    private static func require(_ condition: Bool, _ message: String) throws {
        if !condition { throw APIError(message: message) }
    }

    static func offlineCheck(arguments: [String]) async -> String {
        var folder: URL?
        var report: [String: Any] = [:]
        var step = "initialize diagnostic folder"
        do {
            let idIndex = arguments.firstIndex(of: "--validation-id")
            let rawID = idIndex.flatMap { $0 + 1 < arguments.count ? arguments[$0 + 1] : nil }
            guard let rawID, let id = UUID(uuidString: rawID) else {
                throw APIError(message: "Pass --validation-id followed by a UUID; diagnostics use a separate campaign")
            }
            let root = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                   appropriateFor: nil, create: true)
                .appendingPathComponent("FFBERevival/validation/" + id.uuidString, isDirectory: true)
            folder = root
            try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
            let storage = root.appendingPathComponent("campaign", isDirectory: true)
            let reload = arguments.contains("--offline-self-test-reload")
            if !reload {
                try require(!FileManager.default.fileExists(atPath: storage.appendingPathComponent("campaign.json").path),
                            "Use a new validation UUID for a fresh test")
            }
            step = "Python proof"
            let proof: PythonProof = try await PythonWorker.shared.call(["operation": "hello"])
            try require(proof.answer == 42 && proof.platform == "ios", "Python proof did not execute on iOS")
            let backend = EmbeddedSummonBackend(storage: storage)
            step = "banner catalogue"
            let catalogue = try await backend.banners()
            try require(catalogue.banners.count == 2, "Expected the two authored demo banners")
            step = "initial state"
            let before = try await backend.state()
            if !reload {
                try require(before.currencies["lapis_free"] == 10000 && before.units.count == 2, "Unexpected fresh campaign")
                step = "single summon"
            let single = try await backend.summon(bannerID: "9100203", offer: "primary")
                try require(single.state.currencies["lapis_free"] == 9500 && single.state.units.count == 3,
                            "Single summon debit or collection update failed")
                step = "eleven-pull"
            let multi = try await backend.summon(bannerID: "9100203", offer: "secondary")
                try require(multi.result.awards.count == 11, "Expected eleven awards")
                try require(multi.result.awards.contains { ($0.granted_rarity ?? 0) >= 4 }, "Missing guaranteed rarity")
                var refused = false
                do { _ = try await backend.summon(bannerID: "9100203", offer: "secondary") }
                catch let error as APIError { refused = error.code == "summon_refused" }
                try require(refused, "Unaffordable summon was not refused")
            }
            step = "saved state"
            let after = try await backend.state()
            try require(after.currencies["lapis_free"] == 4500 && after.units.count == 14,
                        "Saved currency or collection mismatch")
            try require(after.last_pull?.awards.count == 11, "Saved results mismatch")
            step = "network diagnostics"
            let diagnostics: Diagnostics = try await PythonWorker.shared.call(["operation": "diagnostics"])
            try require(diagnostics.network_rejected, "Offline network guard failed")
            // iOS may expose /var to Foundation and /private/var to Python.
            let actualSave = URL(fileURLWithPath: diagnostics.save).resolvingSymlinksInPath().path
            let expectedSave = storage.appendingPathComponent("campaign.json").resolvingSymlinksInPath().path
            try require(actualSave == expectedSave, "Save escaped Application Support")
            try require(diagnostics.metadata.contains(".app/PythonApp/metadata/demo"), "Metadata is not bundled")
            report = ["status": "passed", "stage": reload ? "cold-launch-reload" : "summon-and-save",
                      "python": proof.version, "platform": proof.platform,
                      "lapis_free": 4500, "owned_units": 14, "latest_awards": 11,
                      "network_rejected": diagnostics.network_rejected,
                      "save": diagnostics.save, "metadata": diagnostics.metadata,
                      "validation_id": id.uuidString]
        } catch { report = ["status": "failed", "step": step, "error": String(reflecting: error)] }
        if let folder {
            do {
                try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                    .write(to: folder.appendingPathComponent("report.json"), options: .atomic)
            } catch { return "Could not save diagnostic report: " + error.localizedDescription }
        }
        print("Offline diagnostics: \(report)")
        return String(describing: report)
    }
}
