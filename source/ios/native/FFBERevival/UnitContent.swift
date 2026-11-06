import Foundation

struct UnitMetadata: Decodable {
    let name: String?
    let rarity_code: Int?
    let series_root: String?
    let base_rarity_code: Int?
    let max_awakening_rarity_code: Int?
    let artwork: String?
}
private struct UnitCatalogFile: Decodable {
    let schema: Int
    let mode: String
    let units: [String: UnitMetadata]
}
struct UnitDisplay {
    let masterID: String
    let name: String
    let rarity: String
    let metadata: String
    let artworkURL: URL?
}

// Read-only presentation data. Does not mutate a backend, choose rewards or read saves.
final class UnitCatalog {
    static let shared: UnitCatalog? = {
        guard let resources = Bundle.main.resourceURL else { return nil }
        return try? UnitCatalog(directory: resources.appendingPathComponent("UnitContent", isDirectory: true))
    }()
    let directory: URL
    let mode: String
    let units: [String: UnitMetadata]
    var namedCount: Int { units.values.filter { $0.name?.isEmpty == false }.count }
    var artworkCount: Int { units.keys.filter { artworkURL(masterID: $0) != nil }.count }

    init(directory: URL) throws {
        let file = try JSONDecoder().decode(UnitCatalogFile.self,
            from: Data(contentsOf: directory.appendingPathComponent("catalog.json")))
        guard file.schema == 1, ["preservation", "demo"].contains(file.mode) else {
            throw APIError(message: "Unsupported unit content catalog")
        }
        self.directory = directory
        mode = file.mode
        units = file.units
    }
    func artworkURL(masterID: String) -> URL? {
        // Exact form ID only. Never follow a family/root/name as an image fallback.
        guard !masterID.isEmpty, masterID.allSatisfy({ $0.isASCII && $0.isNumber }),
              units[masterID]?.artwork == "sprites/\(masterID).png" else { return nil }
        let url = directory.appendingPathComponent("sprites/\(masterID).png")
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }
    static func rarityLabel(_ code: Int?) -> String {
        guard let code else { return "unknown" }
        // Code 7 spans legacy/NV semantics; don't invent a star/NV interpretation.
        return (1...6).contains(code) ? "\(code)★" : "code \(code)"
    }
    func display(masterID: String, backendName: String?, rarity: Int?, isAward: Bool) -> UnitDisplay {
        let row = units[masterID]
        let name: String
        if mode == "demo", let backendName, !backendName.isEmpty { name = backendName }
        else { name = row?.name.flatMap { $0.isEmpty ? nil : $0 } ?? "Unknown unit (\(masterID))" }
        let current = isAward ? rarity : (row?.rarity_code ?? rarity)
        let rarityText = (isAward ? "Summoned: " : "Rarity: ") + Self.rarityLabel(current)
        let detail = "Base: \(Self.rarityLabel(row?.base_rarity_code)) · Awakening cap: \(Self.rarityLabel(row?.max_awakening_rarity_code))"
        return UnitDisplay(masterID: masterID, name: name, rarity: rarityText,
                           metadata: detail, artworkURL: artworkURL(masterID: masterID))
    }
    static func display(masterID: String, backendName: String?, rarity: Int?, isAward: Bool) -> UnitDisplay {
        if let shared { return shared.display(masterID: masterID, backendName: backendName, rarity: rarity, isAward: isAward) }
        return UnitDisplay(masterID: masterID, name: "Unknown unit (\(masterID))",
                           rarity: (isAward ? "Summoned: " : "Rarity: ") + rarityLabel(rarity),
                           metadata: "Unit content unavailable", artworkURL: nil)
    }
}
