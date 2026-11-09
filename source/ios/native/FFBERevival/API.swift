import Foundation

struct Cost: Decodable {
    let kind: String
    let amount: Int?
    var label: String { if kind == "ticket" { return "Ticket required" }; if kind == "free" { return "Free" }; return "\(amount ?? 0) \(["lapis":"Lapis","lapis_free":"Free Lapis","lapis_paid":"Paid Lapis","friend_point":"Friend Points","gil":"Gil","item":"items","important":"tickets","free":"Free"][kind] ?? kind)" }
}
struct Offer: Decodable, Identifiable {
    let offer: String
    let cost: Cost?
    let draws: Int
    var quote_token: String? = nil
    var id: String { offer }
}
struct Banner: Decodable, Identifiable {
    let id: String
    let name: String
    let supported: Bool
    let offer_details: [Offer]
}
struct UnitRecord: Decodable, Identifiable {
    let instance_id: String
    let master_id: String
    let name: String?
    let level: Int
    let granted_rarity: Int?
    var id: String { instance_id }
}
struct Award: Codable, Identifiable {
    let instance_id: String
    let unit_id: String
    let name: String?
    let granted_rarity: Int?
    var id: String { instance_id }
}
// Legacy awards may carry rarity as either a JSON number or a numeric string,
// particularly when a pull contains another copy of an already-owned unit.
extension Award {
    private enum CodingKeys: String, CodingKey {
        case instance_id, unit_id, name, granted_rarity
    }
    init(from decoder: Decoder) throws {
        let fields = try decoder.container(keyedBy: CodingKeys.self)
        instance_id = try fields.decode(String.self, forKey: .instance_id)
        unit_id = try fields.decode(String.self, forKey: .unit_id)
        name = try fields.decodeIfPresent(String.self, forKey: .name)
        granted_rarity = try fields.decodeLegacyRarity(forKey: .granted_rarity)
    }
}
extension KeyedDecodingContainer {
    func decodeLegacyRarity(forKey key: Key) throws -> Int? {
        if try !contains(key) || decodeNil(forKey: key) { return nil }
        if let number = try? decode(Int.self, forKey: key) { return number }
        // Rarity is presentation metadata, never grounds for rerolling a committed
        // reward. Preserve the award; nil uses the documented blue visual fallback.
        return (try? decode(String.self, forKey: key)).flatMap(Int.init)
    }
}

extension UnitRecord {
    private enum CodingKeys: String, CodingKey { case instance_id, master_id, name, level, granted_rarity }
    init(from decoder: Decoder) throws {
        let fields = try decoder.container(keyedBy: CodingKeys.self)
        instance_id = try fields.decode(String.self, forKey: .instance_id)
        master_id = try fields.decode(String.self, forKey: .master_id)
        name = try fields.decodeIfPresent(String.self, forKey: .name)
        level = try fields.decode(Int.self, forKey: .level)
        granted_rarity = try fields.decodeLegacyRarity(forKey: .granted_rarity)
    }
}
struct Pull: Decodable {
    let awards: [Award]
    let banner_id: String?
    let count: Int?
    init(awards: [Award], banner_id: String? = nil, count: Int? = nil) {
        self.awards = awards; self.banner_id = banner_id; self.count = count
    }
}

// Immutable frontend receipt, created only after one correlated committed response.
// Recovery remains the backend's persisted last_pull, not a second reward store.
struct CommittedSummon: Identifiable {
    let id: UUID
    let bannerID: String
    let offerID: String
    let backendIdentity: String
    let awards: [Award]
    static func sameAwards(_ a: [Award], _ b: [Award]) -> Bool {
        a.count == b.count && zip(a,b).allSatisfy { pair in
            pair.0.instance_id == pair.1.instance_id && pair.0.unit_id == pair.1.unit_id && pair.0.granted_rarity == pair.1.granted_rarity
        }
    }
    static func validated(_ response: SummonResponse, banner: Banner, offer: Offer,
                          identity: String, previousUnits: [UnitRecord]) throws -> CommittedSummon {
        let awards = response.result.awards
        let previous = Set(previousUnits.map(\.instance_id))
        guard !awards.isEmpty, awards.count == offer.draws,
              response.result.banner_id == banner.id,
              response.result.count == offer.draws,
              let saved = response.state.last_pull,
              saved.banner_id == banner.id, saved.count == offer.draws,
              sameAwards(awards,saved.awards),
              Set(awards.map(\.instance_id)).count == awards.count,
              awards.allSatisfy({ award in
                  !award.instance_id.isEmpty && !award.unit_id.isEmpty && !previous.contains(award.instance_id) &&
                  response.state.units.contains { $0.instance_id == award.instance_id && $0.master_id == award.unit_id }
              }) else {
            throw APIError(message: "Summon response could not be correlated with saved awards. Refresh saved state; do not retry automatically.")
        }
        return CommittedSummon(id: UUID(),bannerID: banner.id,offerID: offer.offer,backendIdentity: identity,awards: awards)
    }
}
struct Campaign: Decodable {
    let demo_metadata: Bool
    let currencies: [String: Int]
    let units: [UnitRecord]
    let last_pull: Pull?
}
struct BannersResponse: Decodable { let banners: [Banner] }
struct SummonResponse: Decodable { let result: Pull; let state: Campaign }
struct ServerFailure: Decodable {
    struct Detail: Decodable { let code: String; let message: String }
    let error: Detail
}
struct APIError: LocalizedError {
    let message: String
    var code: String? = nil
    var errorDescription: String? { message }
}

struct API {
    let base: URL
    init(address: String) throws {
        guard let url = URL(string: address.trimmingCharacters(in: .whitespacesAndNewlines)),
              ["http", "https"].contains(url.scheme?.lowercased() ?? ""),
              url.host != nil, url.user == nil, url.password == nil,
              url.query == nil, url.fragment == nil,
              url.path.isEmpty || url.path == "/" else {
            throw APIError(message: "Enter a backend address such as http://192.168.1.20:8765")
        }
        base = url
    }
    func request<T: Decodable>(_ path: String, body: [String: String]? = nil, query: [String: String] = [:]) async throws -> T {
        var components = URLComponents(url: base.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty { components.queryItems = query.sorted(by: {$0.key < $1.key}).map { URLQueryItem(name: $0.key, value: $0.value) } }
        var request = URLRequest(url: components.url!)
        request.timeoutInterval = 20
        request.cachePolicy = .reloadIgnoringLocalCacheData
        if let body {
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError(message: "Invalid server response") }
        guard (200..<300).contains(http.statusCode) else {
            let failure = try? JSONDecoder().decode(ServerFailure.self, from: data)
            throw APIError(message: failure?.error.message ?? "HTTP \(http.statusCode)", code: failure?.error.code)
        }
        return try JSONDecoder().decode(T.self, from: data)
    }
}

protocol SummonBackend {
    func menu() async throws -> MenuCatalog
    func quote(bannerID: String, offer: String) async throws -> MenuQuote
    func banners() async throws -> BannersResponse
    func state() async throws -> Campaign
    func summon(bannerID: String, offer: String) async throws -> SummonResponse
    func summon(bannerID: String, offer: String, quoteToken: String?) async throws -> SummonResponse
}

struct HTTPBackend: SummonBackend {
    private let api: API
    init(address: String) throws { api = try API(address: address) }
    func menu() async throws -> MenuCatalog { try await api.request("v1/menu") }
    func quote(bannerID: String, offer: String) async throws -> MenuQuote { try await api.request("v1/quote", query: ["banner_id":bannerID,"offer":offer]) }
    func banners() async throws -> BannersResponse { try await api.request("v1/banners") }
    func state() async throws -> Campaign { try await api.request("v1/state") }
    func summon(bannerID: String, offer: String) async throws -> SummonResponse {
        try await summon(bannerID:bannerID,offer:offer,quoteToken:nil)
    }
    func summon(bannerID: String, offer: String, quoteToken: String?) async throws -> SummonResponse {
        var body=["banner_id":bannerID,"offer":offer]
        if let quoteToken {body["quote_token"]=quoteToken}
        return try await api.request("v1/summons",body:body)
    }
}

@MainActor
final class SummonModel: ObservableObject {
    @Published var banners: [Banner] = []
    @Published var menuCatalog: MenuCatalog?
    @Published var menuError: String?
    @Published var campaign: Campaign?
    @Published var results: [Award] = []
    @Published var busy = false
    @Published var error: String?
    @Published var needsRefresh = false
    private var connectedIdentity: String?
    private(set) var committedSummon: CommittedSummon?

    func refresh(using backend: any SummonBackend, identity: String) async {
        guard !busy else { return }
        busy = true
        defer { busy = false }
        error = nil
        do {
            let catalogue = try await backend.banners()
            let state = try await backend.state()
            banners = catalogue.banners
            campaign = state
            results = state.last_pull?.awards ?? []
            if let receipt = committedSummon, receipt.backendIdentity != identity || !CommittedSummon.sameAwards(receipt.awards, results) { committedSummon = nil }
            connectedIdentity = identity
            needsRefresh = false
            do { menuCatalog = try await backend.menu(); menuError = nil }
            catch { menuCatalog = nil; menuError = error.localizedDescription }
        } catch {
            self.error = error.localizedDescription
            needsRefresh = true
        }
    }
    @discardableResult
    func summon(_ banner: Banner, offer: Offer, using backend: any SummonBackend, identity: String) async -> Bool {
        guard !busy, !needsRefresh, connectedIdentity == identity else { return false }
        busy = true
        defer { busy = false }
        error = nil
        committedSummon = nil
        let previousUnits = campaign?.units ?? []
        do {
            let response = try await backend.summon(bannerID: banner.id, offer: offer.offer, quoteToken: offer.quote_token)
            guard connectedIdentity == identity else { throw APIError(message: "Backend changed during summon; refresh its saved state.") }
            let receipt = try CommittedSummon.validated(response,banner: banner,offer: offer,identity: identity,previousUnits: previousUnits)
            campaign = response.state
            results = receipt.awards
            committedSummon = receipt
            return true
        } catch {
            self.error = error.localizedDescription + " Refresh saved state before another summon."
            needsRefresh = true
            return false
        }
    }
    func quote(_ bannerID: String, offer: String, using backend: any SummonBackend, identity: String) async -> MenuQuote? {
        guard !busy, !needsRefresh, connectedIdentity == identity else { return nil }
        busy = true
        defer { busy = false }
        do { return try await backend.quote(bannerID: bannerID, offer: offer) }
        catch { self.error = error.localizedDescription; return nil }
    }
    // Preserve the Phase 3 client entry points and contract checks.
    func refresh(_ address: String) async {
        do { await refresh(using: try HTTPBackend(address: address), identity: address) }
        catch { self.error = error.localizedDescription; needsRefresh = true }
    }
    func summon(_ banner: Banner, offer: Offer, address: String) async {
        do { await summon(banner, offer: offer, using: try HTTPBackend(address: address), identity: address) }
        catch { self.error = error.localizedDescription; needsRefresh = true }
    }
    func addressChanged() {
        campaign = nil
        menuCatalog = nil
        banners = []
        results = []
        connectedIdentity = nil
        committedSummon = nil
        needsRefresh = true
    }
}


struct MenuGroup: Decodable, Identifiable { let id: String, label: String }
struct MenuRate: Decodable { let rarity: Int; let weight: Double }
struct MenuTicket: Decodable, Identifiable { let id: String, item_id: String; let balance: Int; let enabled: Bool }
struct MenuQuote: Decodable, Identifiable {
    let banner_id: String, offer: String, detail_id: String
    let draws: Int, balance: Int, step: Int, steps: Int, lap: Int, usage: Int, purchase_limit: Int
    let cost: Cost
    let supported: Bool, eligible: Bool
    let reason: String, guarantee: String, ticket_group: String
    let tickets: [MenuTicket]
    let quote_token: String?
    var id: String { offer }
    var transactionOffer: Offer { Offer(offer: offer,cost: cost,draws: draws,quote_token:quote_token) }
}
struct MenuBanner: Decodable, Identifiable {
    let id: String, name: String, category: String, notice: String, description: String, availability: String
    let groups: [String], featured: [String], offers: [MenuQuote], rates: [MenuRate]
    let playable: Bool
}
struct MenuCatalog: Decodable { let banners: [MenuBanner]; let groups: [MenuGroup] }

extension SummonBackend {
    func summon(bannerID: String, offer: String, quoteToken: String?) async throws -> SummonResponse {
        guard quoteToken == nil else {throw APIError(message:"Backend does not support validated quotes.")}
        return try await summon(bannerID:bannerID,offer:offer)
    }
    func menu() async throws -> MenuCatalog { throw APIError(message: "Update the development backend for banner browsing.") }
    func quote(bannerID: String, offer: String) async throws -> MenuQuote { throw APIError(message: "Live offer quotes are unavailable.") }
}
