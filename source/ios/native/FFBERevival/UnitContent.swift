import Foundation
import CryptoKit

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
        guard !masterID.isEmpty, masterID.allSatisfy({ $0.isASCII && $0.isNumber }) else {return nil}
        if units[masterID]?.artwork == "sprites/\(masterID).png" {
            let url=directory.appendingPathComponent("sprites/\(masterID).png")
            if FileManager.default.fileExists(atPath:url.path) {return url}
        }
        return ExtraUnitArtwork.url(masterID)
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

// Supplemental exact-form files only; never follow a name or a family/root ID.
enum ExtraUnitArtwork {
    static let expectedLock="4564564bc8d43f7ee946408dd46f82cd357a0f2bc6c5b5543275bb25e7c3c63f"
    private static let root=Bundle.main.resourceURL?.appendingPathComponent("ExtraUnitArt")
    private static let manifest:[String:[String:String]] = {
        guard let root,let raw=try? Data(contentsOf:root.appendingPathComponent("receipt.json")),
              let receipt=try? JSONSerialization.jsonObject(with:raw) as? [String:Any],receipt["lock_sha256"] as? String==expectedLock,
              let files=receipt["files"] as? [String:String],let data=try? Data(contentsOf:root.appendingPathComponent("catalog.json")),
              files["catalog.json"]==SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined(),
              let rows=try? JSONSerialization.jsonObject(with:data) as? [String:[String:String]],rows.count<=32 else {return [:]}
        return rows
    }()
    static var availableIDs:Set<String> {Set(manifest.keys)}
    static func url(_ id:String)->URL? {
        guard id.allSatisfy({$0.isASCII && $0.isNumber}),let row=manifest[id],row["file"]=="sprites/\(id).png",let root,
              let data=try? Data(contentsOf:root.appendingPathComponent("sprites/\(id).png")),data.count<=128*1024,
              row["sha256"]==SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined() else {return nil}
        return root.appendingPathComponent("sprites/\(id).png")
    }
}
