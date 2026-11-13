// Hotel Paradiso Arcade: a full-screen, mouse-only menu for the two Hotel Paradiso games and
// Do Not Disturb, meant to be the only thing on a kiosk Mac (macOS 10.15 and later).
//
// The games live inside this app's Resources folder:
//   ScummVM.app                      plays both point-and-clicks
//   DoNotDisturb.app                 the Ren'Py visual novel
//   games/hotel-paradiso/            tentacle.000, tentacle.001
//   games/sacra-pasta/               sacrapasta.ags
//   art/<id>.png                     the picture on each card
//
// While the menu is in front: no Dock, no menu bar, no Cmd-Tab, no Force Quit window and no
// log-out shortcut. Clicking a card starts that game full screen; quitting the game brings the
// menu back. To leave the menu, press Control-Option-Command-Q and type the exit code: the first
// line of ~/Library/Application Support/Hotel Paradiso Arcade/exit-code.txt if that exists,
// otherwise the ArcadeExitCode key in Info.plist ("paradiso").

import AppKit

struct Game {
    let id: String
    let title: String
    let subtitle: String
    let blurb: String
}

let GAMES = [
    Game(id: "hotel-paradiso", title: "Hotel Paradiso", subtitle: "Room 714",
         blurb: "There's a party on the ninth floor, and you are in no state to go. Yet."),
    Game(id: "sacra-pasta", title: "Hotel Paradiso", subtitle: "Sacra Pasta",
         blurb: "Room 913 has become a shrine to the noodle. Join the church. Become Pope."),
    Game(id: "do-not-disturb", title: "Do Not Disturb", subtitle: "Three nights at the Hotel Paradiso",
         blurb: "A secret party, a hotel full of art rooms, and a ceremony at 11:11."),
]

// ------------------------------------------------------------------ colours and fonts
let NIGHT = NSColor(calibratedRed: 0.07, green: 0.05, blue: 0.12, alpha: 1)
let NIGHT_LO = NSColor(calibratedRed: 0.16, green: 0.07, blue: 0.20, alpha: 1)
let NEON = NSColor(calibratedRed: 1.00, green: 0.42, blue: 0.70, alpha: 1)
let GOLD = NSColor(calibratedRed: 1.00, green: 0.83, blue: 0.45, alpha: 1)
let CREAM = NSColor(calibratedRed: 0.96, green: 0.92, blue: 0.86, alpha: 1)
let DIM = NSColor(calibratedRed: 0.70, green: 0.64, blue: 0.74, alpha: 1)

func font(_ size: CGFloat, bold: Bool = false) -> NSFont {
    for name in bold ? ["AvenirNext-Heavy", "Futura-Bold"] : ["AvenirNext-Medium", "Futura-Medium"] {
        if let f = NSFont(name: name, size: size) { return f }
    }
    return bold ? NSFont.boldSystemFont(ofSize: size) : NSFont.systemFont(ofSize: size)
}

func drawText(_ s: String, _ f: NSFont, _ c: NSColor, in r: NSRect, align: NSTextAlignment = .center, glow: NSColor? = nil) {
    let p = NSMutableParagraphStyle()
    p.alignment = align
    p.lineBreakMode = .byWordWrapping
    var attrs: [NSAttributedString.Key: Any] = [.font: f, .foregroundColor: c, .paragraphStyle: p]
    if let g = glow {
        let sh = NSShadow()
        sh.shadowColor = g
        sh.shadowBlurRadius = f.pointSize * 0.35
        sh.shadowOffset = .zero
        attrs[.shadow] = sh
    }
    (s as NSString).draw(with: r, options: [.usesLineFragmentOrigin], attributes: attrs)
}

// ------------------------------------------------------------------ one game's card
final class CardView: NSView {
    let game: Game
    let image: NSImage?
    var onClick: (() -> Void)?
    var hover = false { didSet { needsDisplay = true } }
    var busy = false { didSet { needsDisplay = true } }

    init(game: Game, image: NSImage?) {
        self.game = game
        self.image = image
        super.init(frame: .zero)
    }
    required init?(coder: NSCoder) { fatalError() }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        for t in trackingAreas { removeTrackingArea(t) }
        addTrackingArea(NSTrackingArea(rect: bounds, options: [.mouseEnteredAndExited, .activeAlways, .inVisibleRect],
                                       owner: self, userInfo: nil))
    }
    override func mouseEntered(with event: NSEvent) { hover = true }
    override func mouseExited(with event: NSEvent) { hover = false }
    override func mouseDown(with event: NSEvent) { if !busy { onClick?() } }
    override func resetCursorRects() { addCursorRect(bounds, cursor: .pointingHand) }

    override func draw(_ dirtyRect: NSRect) {
        let r = bounds.insetBy(dx: 6, dy: 6)
        let card = NSBezierPath(roundedRect: r, xRadius: 14, yRadius: 14)
        NSColor(calibratedWhite: 0, alpha: 0.35).setFill()
        card.fill()
        // the picture: the top part of the card, cropped to fill
        let picH = r.width * 9 / 16
        let pic = NSRect(x: r.minX, y: r.maxY - picH, width: r.width, height: picH)
        NSGraphicsContext.saveGraphicsState()
        let clip = NSBezierPath()
        clip.appendRoundedRect(pic, xRadius: 14, yRadius: 14)
        clip.append(NSBezierPath(rect: NSRect(x: pic.minX, y: pic.minY, width: pic.width, height: 16)))
        clip.addClip()
        if let img = image, img.size.width > 0 {
            let s = max(pic.width / img.size.width, pic.height / img.size.height)
            let w = img.size.width * s, h = img.size.height * s
            NSGraphicsContext.current?.imageInterpolation = .none     // keep the pixel art crisp
            img.draw(in: NSRect(x: pic.midX - w / 2, y: pic.midY - h / 2, width: w, height: h))
        } else {
            NIGHT_LO.setFill()
            pic.fill()
        }
        NSGraphicsContext.restoreGraphicsState()
        // the words
        let pad = r.width * 0.06
        let tr = NSRect(x: r.minX + pad, y: r.minY + pad, width: r.width - 2 * pad, height: pic.minY - r.minY - 2 * pad)
        let ts = max(18, r.width * 0.075)
        drawText(game.title, font(ts, bold: true), hover ? GOLD : CREAM,
                 in: NSRect(x: tr.minX, y: tr.maxY - ts * 1.3, width: tr.width, height: ts * 1.4), align: .left)
        drawText(game.subtitle, font(ts * 0.62, bold: true), NEON,
                 in: NSRect(x: tr.minX, y: tr.maxY - ts * 2.25, width: tr.width, height: ts), align: .left)
        drawText(game.blurb, font(ts * 0.5), DIM,
                 in: NSRect(x: tr.minX, y: tr.minY, width: tr.width, height: tr.height - ts * 2.5), align: .left)
        // the frame: gold when the mouse is over it
        card.lineWidth = hover ? 4 : 2
        (hover ? GOLD : NSColor(calibratedWhite: 1, alpha: 0.15)).setStroke()
        card.stroke()
        if busy {
            NSColor(calibratedWhite: 0, alpha: 0.55).setFill()
            card.fill()
        }
    }
}

// ------------------------------------------------------------------ the whole screen
final class MenuView: NSView {
    var cards: [CardView] = []
    var status = "" { didSet { needsDisplay = true } }

    override var isFlipped: Bool { false }

    override func layout() {
        super.layout()
        let n = CGFloat(cards.count)
        let gap = bounds.width * 0.025
        let cw = min((bounds.width * 0.9 - gap * (n - 1)) / n, 520)
        let ch = cw * 9 / 16 + cw * 0.5
        let total = cw * n + gap * (n - 1)
        var x = bounds.midX - total / 2
        let y = bounds.midY - ch / 2 - bounds.height * 0.04
        for c in cards {
            c.frame = NSRect(x: x, y: y, width: cw, height: ch)
            x += cw + gap
        }
    }

    override func draw(_ dirtyRect: NSRect) {
        NSGradient(starting: NIGHT_LO, ending: NIGHT)?.draw(in: bounds, angle: 90)
        // a few stars
        var seed: UInt64 = 714
        for _ in 0..<90 {
            seed = seed &* 6364136223846793005 &+ 1442695040888963407
            let x = CGFloat(seed >> 33 & 0xFFFF) / 65535 * bounds.width
            seed = seed &* 6364136223846793005 &+ 1442695040888963407
            let y = bounds.height * (0.55 + 0.45 * CGFloat(seed >> 33 & 0xFFFF) / 65535)
            NSColor(calibratedWhite: 1, alpha: 0.35).setFill()
            NSRect(x: x, y: y, width: 2, height: 2).fill()
        }
        let h = bounds.height
        drawText("HOTEL PARADISO", font(h * 0.085, bold: true), NEON,
                 in: NSRect(x: 0, y: h * 0.80, width: bounds.width, height: h * 0.12), glow: NEON)
        drawText("ARCADE", font(h * 0.032, bold: true), GOLD,
                 in: NSRect(x: 0, y: h * 0.755, width: bounds.width, height: h * 0.05))
        let foot = status.isEmpty ? "Click a game to play. When you quit the game, you come back here." : status
        drawText(foot, font(max(14, h * 0.022)), DIM, in: NSRect(x: 0, y: h * 0.05, width: bounds.width, height: h * 0.05))
    }
}

// ------------------------------------------------------------------ the app
final class KioskWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

final class Arcade: NSObject, NSApplicationDelegate {
    var window: KioskWindow!
    var menu: MenuView!
    var running: Process?
    var allowQuit = false
    let res = URL(fileURLWithPath: Bundle.main.resourcePath ?? ".")
    var support: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory())
        return base.appendingPathComponent("Hotel Paradiso Arcade")
    }

    func kiosk() {
        NSApp.presentationOptions = [.hideDock, .hideMenuBar, .disableProcessSwitching, .disableForceQuit,
                                     .disableSessionTermination, .disableHideApplication, .disableAppleMenu]
    }

    func applicationDidFinishLaunching(_ note: Notification) {
        try? FileManager.default.createDirectory(at: support.appendingPathComponent("saves"), withIntermediateDirectories: true)
        writeScummVMConfig()
        kiosk()
        let screen = NSScreen.main?.frame ?? NSRect(x: 0, y: 0, width: 1280, height: 800)
        window = KioskWindow(contentRect: screen, styleMask: [.borderless], backing: .buffered, defer: false)
        window.backgroundColor = NIGHT
        window.isMovable = false
        window.collectionBehavior = [.fullScreenPrimary, .stationary]
        menu = MenuView(frame: NSRect(origin: .zero, size: screen.size))
        for g in GAMES {
            let img = NSImage(contentsOf: res.appendingPathComponent("art/\(g.id).png"))
            let c = CardView(game: g, image: img)
            c.onClick = { [weak self] in self?.play(g) }
            menu.addSubview(c)
            menu.cards.append(c)
        }
        window.contentView = menu
        window.setFrame(screen, display: true)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        NSCursor.unhide()
        // the way out, for whoever looks after the machine
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] e in
            let mods = e.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if mods.contains([.control, .option, .command]) && e.charactersIgnoringModifiers?.lowercased() == "q" {
                self?.askToQuit()
                return nil
            }
            return e
        }
        // the screen changing size (a projector plugged in, say)
        NotificationCenter.default.addObserver(forName: NSApplication.didChangeScreenParametersNotification, object: nil,
                                               queue: .main) { [weak self] _ in
            if let s = NSScreen.main?.frame { self?.window.setFrame(s, display: true) }
        }
        // if anything else comes to the front while no game is running, take the screen back
        NSWorkspace.shared.notificationCenter.addObserver(forName: NSWorkspace.didActivateApplicationNotification, object: nil,
                                                          queue: .main) { [weak self] n in
            guard let self = self, self.running == nil, !self.allowQuit else { return }
            let app = n.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
            if app?.processIdentifier != ProcessInfo.processInfo.processIdentifier {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { self.comeBack() }
            }
        }
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        return allowQuit ? .terminateNow : .terminateCancel
    }

    func writeScummVMConfig() {
        let ini = support.appendingPathComponent("scummvm.ini")
        let saves = support.appendingPathComponent("saves").path
        // rewritten every start, so a visitor can't leave ScummVM set up differently
        let text = """
        [scummvm]
        gui_return_to_launcher_at_exit=false
        confirm_exit=false
        fullscreen=true
        savepath=\(saves)
        updates_check=0
        gui_browser_native=false
        """
        try? text.write(to: ini, atomically: true, encoding: .utf8)
    }

    func play(_ g: Game) {
        guard running == nil else { return }
        let p = Process()
        switch g.id {
        case "do-not-disturb":
            guard let exe = Bundle(url: res.appendingPathComponent("DoNotDisturb.app"))?.executableURL else { return fail(g) }
            p.executableURL = exe
            p.arguments = []
        default:
            guard let exe = Bundle(url: res.appendingPathComponent("ScummVM.app"))?.executableURL else { return fail(g) }
            p.executableURL = exe
            let dir = res.appendingPathComponent("games/\(g.id)").path
            var args = ["--config=\(support.appendingPathComponent("scummvm.ini").path)",
                        "--savepath=\(support.appendingPathComponent("saves").path)",
                        "--fullscreen", "--path=\(dir)"]
            if g.id == "hotel-paradiso" { args.append("tentacle") }
            else { args += ["--no-aspect-ratio", "--auto-detect"] }
            p.arguments = args
        }
        p.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async { self?.gameOver() }
        }
        do {
            try p.run()
        } catch {
            return fail(g)
        }
        running = p
        for c in menu.cards { c.busy = true }
        menu.status = "Starting \(g.subtitle)…"
    }

    func fail(_ g: Game) {
        menu.status = "\(g.subtitle) couldn't start. Please let a grown-up know."
    }

    func gameOver() {
        running = nil
        for c in menu.cards { c.busy = false; c.hover = false }
        menu.status = ""
        comeBack()
    }

    func comeBack() {
        kiosk()
        NSApp.activate(ignoringOtherApps: true)
        window.makeKeyAndOrderFront(nil)
    }

    func askToQuit() {
        // exit-code.txt in the arcade's support folder, if someone's set one; otherwise Info.plist's
        var code = (Bundle.main.object(forInfoDictionaryKey: "ArcadeExitCode") as? String) ?? "paradiso"
        if let s = try? String(contentsOf: support.appendingPathComponent("exit-code.txt"), encoding: .utf8) {
            let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
            if !t.isEmpty { code = t }
        }
        let a = NSAlert()
        a.messageText = "Leave the arcade?"
        a.informativeText = "Type the exit code to quit Hotel Paradiso Arcade."
        let field = NSSecureTextField(frame: NSRect(x: 0, y: 0, width: 240, height: 24))
        a.accessoryView = field
        a.addButton(withTitle: "Quit")
        a.addButton(withTitle: "Cancel")
        a.window.initialFirstResponder = field
        if a.runModal() == .alertFirstButtonReturn && field.stringValue == code {
            allowQuit = true
            NSApp.presentationOptions = []
            running?.terminate()
            NSApp.terminate(nil)
        }
    }
}

let app = NSApplication.shared
let arcade = Arcade()
app.delegate = arcade
app.setActivationPolicy(.regular)
app.run()
