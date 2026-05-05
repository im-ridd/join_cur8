"""Email validation utilities: format check and trusted-provider whitelist."""
import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic format validation
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email_format(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


# ---------------------------------------------------------------------------
# Trusted email provider whitelist
# Only major, well-known providers accepted — prevents obscure/throwaway domains.
# ---------------------------------------------------------------------------
TRUSTED_DOMAINS: set[str] = {
    # Google
    "gmail.com", "googlemail.com",
    # Microsoft
    "outlook.com", "outlook.it", "outlook.fr", "outlook.de", "outlook.es",
    "outlook.co.uk", "outlook.com.br", "outlook.jp", "outlook.in",
    "hotmail.com", "hotmail.it", "hotmail.fr", "hotmail.de", "hotmail.es",
    "hotmail.co.uk", "hotmail.com.br", "hotmail.co.jp", "hotmail.be",
    "hotmail.nl", "hotmail.se", "hotmail.dk", "hotmail.no", "hotmail.fi",
    "live.com", "live.it", "live.fr", "live.de", "live.es",
    "live.co.uk", "live.com.br", "live.nl", "live.be", "live.se",
    "msn.com",
    # Yahoo
    "yahoo.com", "yahoo.it", "yahoo.fr", "yahoo.de", "yahoo.es",
    "yahoo.co.uk", "yahoo.co.jp", "yahoo.com.br", "yahoo.com.au",
    "yahoo.in", "yahoo.com.mx", "yahoo.com.ar", "yahoo.gr",
    "yahoo.ro", "yahoo.pl", "yahoo.at", "yahoo.dk", "yahoo.se",
    "yahoo.no", "yahoo.fi", "yahoo.com.hk", "yahoo.com.sg",
    "ymail.com", "rocketmail.com",
    # Apple
    "icloud.com", "me.com", "mac.com",
    # ProtonMail
    "protonmail.com", "protonmail.ch", "proton.me", "pm.me",
    # Tutanota / Tuta
    "tutanota.com", "tutanota.de", "tutamail.com", "tuta.io", "keemail.me",
    # Fastmail
    "fastmail.com", "fastmail.fm", "fastmail.org", "fastmail.net",
    "fastmail.to", "fastmail.cn", "fastmail.es", "fastmail.de",
    "fastmail.in", "fastmail.jp", "fastmail.se", "fastmail.to",
    # Zoho
    "zoho.com", "zohomail.com",
    # AOL / Verizon
    "aol.com", "aol.co.uk", "aol.fr", "aol.de", "aol.it",
    "verizon.net", "aim.com",
    # GMX
    "gmx.com", "gmx.de", "gmx.at", "gmx.ch", "gmx.net",
    "gmx.fr", "gmx.us", "gmx.org", "gmx.info",
    # Web.de
    "web.de",
    # Mail.com
    "mail.com", "email.com", "usa.com", "myself.com",
    # Libero (Italy)
    "libero.it", "inwind.it", "blu.it", "giallo.it", "iol.it",
    # Alice / TIM (Italy)
    "alice.it", "tim.it",
    # Virgilio (Italy)
    "virgilio.it",
    # Tiscali (Italy)
    "tiscali.it",
    # Fastweb (Italy)
    "fastwebnet.it",
    # Wind (Italy)
    "windtre.it",
    # Telecom Italia
    "tin.it",
    # Poste Italiane
    "poste.it",
    # Freenet (Germany)
    "freenet.de",
    # T-Online (Germany)
    "t-online.de",
    # Orange / Wanadoo (France)
    "orange.fr", "wanadoo.fr", "laposte.net", "sfr.fr", "free.fr",
    "bbox.fr", "numericable.fr",
    # Telefonica (Spain)
    "telefonica.net", "terra.es", "movistar.es",
    # BT (UK)
    "btinternet.com", "btopenworld.com", "bt.com",
    # Sky (UK)
    "sky.com", "skynet.be",
    # Virgin Media (UK)
    "virginmedia.com",
    # Talktalk (UK)
    "talktalk.net",
    # NTT / Docomo (Japan)
    "docomo.ne.jp", "au.com", "softbank.ne.jp",
    # Naver (Korea)
    "naver.com",
    # Daum / Kakao (Korea)
    "daum.net", "kakao.com",
    # Yandex (Russia)
    "yandex.ru", "yandex.com", "yandex.ua", "yandex.by", "yandex.kz",
    "ya.ru",
    # Mail.ru
    "mail.ru", "list.ru", "inbox.ru", "bk.ru",
    # UOL (Brazil)
    "uol.com.br", "bol.com.br",
    # iG (Brazil)
    "ig.com.br",
    # Sina (China)
    "sina.com", "sina.cn",
    # 163 / 126 / Yeah (China)
    "163.com", "126.com", "yeah.net",
    # QQ (China) - major/legitimate
    "qq.com",
    # Rediff (India)
    "rediffmail.com",
    # Ukr.net (Ukraine)
    "ukr.net",
    # i.ua (Ukraine)
    "i.ua",
    # Sapo (Portugal)
    "sapo.pt",
    # Hushmail (privacy, legitimate)
    "hushmail.com",
    # Mailfence
    "mailfence.com",
    # Startmail
    "startmail.com",
    # Runbox
    "runbox.com",
    # Posteo
    "posteo.de", "posteo.net", "posteo.org",
    # Skiff
    "skiff.com",
}


def is_trusted_email_domain(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in TRUSTED_DOMAINS


# ---------------------------------------------------------------------------
# Combined check
# ---------------------------------------------------------------------------
def validate_email_address(email: str) -> str | None:
    """
    Returns an error string if the email is invalid/blocked, or None if OK.
    """
    email = email.strip().lower()

    if not is_valid_email_format(email):
        return "Invalid email address format"

    if not is_trusted_email_domain(email):
        return "Please use a major email provider (Gmail, Outlook, Yahoo, iCloud, etc.)"

    return None


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic format validation
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email_format(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


# ---------------------------------------------------------------------------
# Disposable / temporary email domain blacklist
# ---------------------------------------------------------------------------
DISPOSABLE_DOMAINS: set[str] = {
    # ── well-known throwaway services ────────────────────────────────────────
    "mailinator.com", "guerrillamail.com", "guerrillamail.info",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.net",
    "guerrillamail.org", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "guerrillamail.app", "spam4.me", "trashmail.com",
    "trashmail.at", "trashmail.io", "trashmail.me", "trashmail.net",
    "trashmail.org", "dispostable.com", "mailnull.com",
    "yopmail.com", "yopmail.fr", "cool.fr.nf", "jetable.fr.nf",
    "nospam.ze.tc", "nomail.xl.cx", "mega.zik.dj", "speed.1s.fr",
    "courriel.fr.nf", "moncourrier.fr.nf", "monemail.fr.nf",
    "monmail.fr.fr", "tempr.email", "discard.email",
    "spamgourmet.com", "spamgourmet.net", "spamgourmet.org",
    "spamcorpse.com", "mailexpire.com", "maildrop.cc",
    "throwam.com", "throwaway.email", "tempinbox.com",
    "fakeinbox.com", "spamfree24.org", "spamfree24.de",
    "spam.la", "bspamfree.org", "spamfree.eu",
    "spamspot.com", "spamthisplease.com",
    "10minutemail.com", "10minutemail.net", "10minutemail.org",
    "10minutemail.co.uk", "10minutemail.de", "10minutemail.eu",
    "10minutemail.nl", "10minutemail.ru", "10minutemail.us",
    "10minemail.com", "20minutemail.com", "30minutemail.com",
    "filzmail.com", "throwam.com", "throwawayemailaddress.com",
    "mailnesia.com", "mailnull.com", "mailsac.com",
    "tempmailaddress.com", "tempmail.com", "tempmail.net",
    "tempmail.org", "temp-mail.org", "temp-mail.ru",
    "temp-mail.io", "tempmailo.com", "tmpmail.net",
    "tmpmail.org", "tmpjr.me", "jetable.com",
    "jetable.net", "jetable.org", "jetable.pp.ua",
    "notsharingmy.info", "objectmail.com", "ownmail.net",
    "pecinan.com", "pecinan.net", "pecinan.org",
    "sharedmailbox.org", "spamevader.com", "spambob.com",
    "spambob.net", "spambob.org", "spambog.com",
    "spambog.de", "spambog.ru", "spamday.com",
    "spamgap.com", "spamgap.net", "spamgap.org",
    "spamhereplease.com", "spamhole.com",
    "spamingbot.com", "spamoff.de", "spamslicer.com",
    "spamstack.net", "spamthis.co.uk",
    "mohmal.com", "mailmoat.com", "mailnew.com",
    "crazymailing.com", "dispostable.com",
    "tempinbox.co.uk", "tempinbox.com",
    "throwam.com", "fake-box.com", "fakemailgenerator.com",
    "anonymbox.com", "antispam24.de", "bofthew.com",
    "bouncr.com", "breakthru.com",
    "bund.us", "byom.de", "casualdx.com",
    "centermail.com", "centermail.net",
    "chongmail.com", "clixser.com", "clrmail.com",
    "cmail.club", "cmail.com", "cmail.net",
    "cock.li", "coffeetimer24.com", "coieo.com",
    "coolimpool.org", "courriel.tv",
    "cuvox.de", "dayrep.com", "deadaddress.com",
    "deadletter.ga", "deagot.com", "dealja.com",
    "despam.it", "devnullmail.com", "dharmatel.net",
    "digitalsanctuary.com", "dingbone.com",
    "discardmail.com", "discardmail.de",
    "discard.ga", "disposableemailaddresses.com",
    "disposable.com", "disposeamail.com",
    "dlemail.ru", "dodgeit.com", "dodgit.com",
    "donemail.ru", "dontsendmespam.de", "drdrb.com",
    "drdrb.net", "dump-email.info", "dumpandfuck.com",
    "dumpmail.de", "dumpyemail.com", "easytrashmail.com",
    "edgex.ru", "email60.com", "emailfake.com",
    "emailias.com", "emailigo.com", "emailinfive.com",
    "emaillime.com", "emailproxsy.com", "emailresort.com",
    "emailsensei.com", "emailtemporanea.com", "emailtemporany.com",
    "emailtemporanea.net", "emailto.de", "emailwarden.com",
    "emailx.at.hm", "emailxfer.com", "emeil.in",
    "emeil.ir", "emz.net", "enterto.com",
    "eqiluxspam.ga", "escapehatch.it", "e-tobet.com",
    "evopo.com", "explodemail.com", "express.net.ua",
    "eyepaste.com", "fakedemail.com", "fakemails.cf",
    "fakemails.ga", "fakemails.gq", "fakemails.ml",
    "fastacura.com", "fastchevy.com", "fastchrysler.com",
    "fastkawasaki.com", "fastmazda.com", "fastmitsubishi.com",
    "fastnissan.com", "fastsubaru.com", "fastsuzuki.com",
    "fasttoyota.com", "fastyamaha.com",
    "filzmail.de", "fleckens.hu", "fmailbox.com",
    "fmailc.com", "fmails.com", "fnmail.com",
    "fr33mail.info", "frapmail.com", "freundin.ru",
    "front14.org", "fudgerub.com", "fux0ringduh.com",
    "fxnxs.com", "fyii.de", "garliclife.com",
    "get1mail.com", "get2mail.fr", "getairmail.com",
    "geteit.com", "getmails.eu", "getonemail.com",
    "getonemail.net", "ghost-email.com", "ghostmail.de",
    "giantmail.de", "girlsundertheinfluence.com",
    "gishpuppy.com", "glitch.sx",
    "goemailgo.com", "gotmail.com", "gotmail.net",
    "gotmail.org", "grainne.com", "guestmail.com",
    "gustr.com", "h.mintemail.com", "h8s.org",
    "haltospam.com", "hatespam.org", "herp.in",
    "hidemail.de", "hidzz.com", "hochsitze.com",
    "hocus-bogus.com", "holla.de",
    "hostguru.info", "hotpop.com", "hulapla.de",
    "hushmail.com",  # note: hushmail legitimate for privacy but often abused
    "hvastudiesucces.nl", "ieatspam.eu", "ieatspam.info",
    "ieh-mail.de", "ignoremail.com", "ihateyoualot.info",
    "iheartspam.org", "imails.info", "inboxalias.com",
    "inboxclean.com", "inboxclean.org", "incognitomail.com",
    "incognitomail.net", "incognitomail.org",
    "inoutmail.de", "inoutmail.eu", "inoutmail.info",
    "inoutmail.net", "intam.net", "internet-e-mail.de",
    "internet-mail.de", "internetemails.net",
    "iodizc.com", "isposable.com", "it-dienste.eu",
    "iwi.net", "j-p.us", "jnxjn.com",
    "joelonsoftware.net", "joker.com", "junk1.tk",
    "junkmail.com", "junkmail.ga", "junkmail.gq",
    "junkmail.gr", "junkmail.io", "junkmail.ml",
    "kasmail.com", "kaspop.com", "killmail.com",
    "killmail.net", "klassmaster.com", "klassmaster.net",
    "klassmaster.org", "klzlk.com", "koszmail.pl",
    "kurzepost.de", "kutakbisagitu.com",
    "l33r.eu", "lawlita.com", "lazyinbox.com",
    "letthemeatspam.com", "lhsdv.com", "ligsb.com",
    "lol.ovpn.to", "lolfreak.net", "lookugly.com",
    "lortemail.dk", "losemymail.com", "lovemeleaveme.com",
    "lovemeleaveme.org", "lr78.com", "lukop.dk",
    "lyricspad.net", "m21.cc", "maboard.com",
    "mail-filter.com", "mail-temporaire.fr",
    "mail.by", "mail.mezimages.net",
    "mail114.net", "mail1a.de", "mail21.cc",
    "mail2rss.org", "mail333.com",
    "mailbidon.com", "mailbiz.biz", "mailblocks.com",
    "mailbucket.org", "mailcat.biz", "mailcatch.com",
    "mailde.de", "mailde.info", "maildu.de",
    "maileater.com", "mailed.ro", "maileme101.com",
    "mailf5.com", "mailfall.com", "mailforspam.com",
    "mailfreeonline.com", "mailguard.me", "mailhazard.com",
    "mailhazard.us", "mailimate.com", "mailin8r.com",
    "mailinater.com", "mailinator.net", "mailinator.org",
    "mailinator.us", "mailinatorlists.com",
    "mailismagic.com", "mailme.ir", "mailme.lv",
    "mailme24.com", "mailmetrash.com", "mailmich.com",
    "mailna.biz", "mailna.co", "mailna.in",
    "mailna.me", "mailnull.com", "mailpick.biz",
    "mailproxsy.com", "mailquack.com", "mailrock.biz",
    "mailscrap.com", "mailshell.com", "mailsiphon.com",
    "mailslite.com", "mailspam.me", "mailspam.net",
    "mailspam.xyz", "mailstart.com", "mailstartplus.com",
    "mailsucker.net", "mailtome.de", "mailtothis.com",
    "mailtrash.net", "mailtv.net", "mailtv.tv",
    "mailvault.com", "mailw.info", "mailwithyou.com",
    "mailzilla.com", "mailzilla.org", "mbx.cc",
    "mega.zik.dj", "meltmail.com", "messagebeamer.de",
    "mierdamail.com", "mintemail.com", "misterpinball.de",
    "mmsms.info", "moncourrier.fr.nf",
    "monkemail.com", "moncourrier.fr.nf",
    "motique.de", "mountainregionallibrary.net",
    "mswork.ru", "mt2009.com", "mt2014.com",
    "muell.de", "muell.email", "muell.io",
    "muell.icu", "muell.monster",
    "mvrht.com", "mvrht.net", "myfastmail.com",
    "mypacks.net", "mypartyclip.de", "myphantomemail.com",
    "myspaceinc.com", "myspaceinc.net", "myspaceinc.org",
    "myspacepimpedup.com", "myspamless.com", "mytempemail.com",
    "mytrashmail.com", "nada.email", "nada.ltd",
    "netmails.com", "netmails.net", "netvision.net.il",
    "newmail.ru", "no-spam.ws", "noblepioneer.com",
    "nobulk.com", "noclickemail.com", "nodezine.com",
    "nogmailspam.info", "nomorespamhere.com",
    "nonspam.eu", "nonspammer.de", "noref.in",
    "nospam.ze.tc", "nospamfor.us", "nospammail.net",
    "nospamme.com", "notsharingmy.info", "nowhere.org",
    "ntlm.in", "nwldx.com", "objectmail.com",
    "obobbo.com", "odaymail.com", "oi.com.br",  # remove if needed
    "one-time.email", "oneoffmail.com", "onewaymail.com",
    "online.ms", "opentrash.com", "opojix.xyz",
    "ordinaryamerican.net", "orgmbx.cc",
    "ownmail.net", "owlpic.com",
    "paplease.com", "para2019.club", "pastebitch.com",
    "pjjkp.com", "plexolan.de", "pm.com",
    "politikerclub.de", "pookmail.com", "pop3.xyz",
    "porsh.net", "posta.store", "pr7.net",
    "proxymail.eu", "prtnx.com", "prtz.eu",
    "punkass.com", "putthisinyourspamdatabase.com",
    "pwrby.com", "qq.com",  # abused for spam
    "quickinbox.com", "queuem.com", "qvy.me",
    "rcpt.at", "reallymymail.com", "reallymymaildelivery.com",
    "recode.me", "rectifier.net",
    "recyclemail.dk", "regbypass.comsafe-mail.net",
    "regspaces.tk", "reliable-mail.com", "relayfix.com",
    "remail.cf", "remail.ga", "removeyourself.com",
    "rhyta.com", "rofl.mr", "rppkn.com",
    "rtrtr.com", "ruffrey.com", "ruu.kr",
    "s0ny.net", "safe-mail.net",
    "safetymail.info", "safetypost.de",
    "sanfinder.com", "saynotospams.com",
    "selfdestructingmail.com", "sendspamhere.com",
    "services391.com", "sharklasers.com", "sharedmailbox.org",
    "shitmail.de", "shitmail.me", "shitmail.org",
    "shitware.nl", "skeefmail.com", "slapsfromlastnight.com",
    "slaskpost.se", "slow-email.com", "slopsbox.com",
    "smellfear.com", "smnmedia.com",
    "snakemail.com", "sneakemail.com", "sofimail.com",
    "sofort-mail.de", "sogetthis.com", "soisz.com",
    "spam.la", "spam.mn", "spam.org.tr",
    "spam.su", "spam4.me", "spamail.de",
    "spamavert.com", "spambox.info", "spambox.irishspringrealty.com",
    "spambox.us", "spamcatcher.net", "spamcon.org",
    "spamcorpse.com", "spamex.com",
    "spamfree24.de", "spamfree24.eu", "spamfree24.info",
    "spamfree24.net", "spamfree24.org",
    "spamgoes.in", "spamgourmet.com", "spamgourmet.net",
    "spamgourmet.org", "spamherelots.com",
    "spamhereplease.com", "spamhole.com", "spaml.com",
    "spaml.de", "spammotel.com", "spamobox.com",
    "spamoff.de", "spamspot.com", "spamstack.net",
    "spamthis.co.uk", "spamthisplease.com", "spamtrail.com",
    "speed.1s.fr", "spikio.com",
    "spoofmail.de", "squizzy.de", "squizzy.eu",
    "squizzy.net", "stinkefinger.net",
    "stuffmail.de", "super-auswahl.de", "supergreatmail.com",
    "supermailer.jp", "superrito.com", "superspeedy.nl",
    "suremail.info", "svk.jp", "sweetxxx.de",
    "tafmail.com", "tagyourself.com", "talkinator.com",
    "tapchicuoihoi.com", "tefl.ro", "teleworm.com",
    "teleworm.us", "tempalias.com", "tempe-mail.com",
    "tempemail.biz", "tempemail.com",
    "tempemail.net", "tempemail.org", "temporamail.net",
    "temporaryemail.net", "temporaryemail.us",
    "temporaryinbox.com", "tempymail.com", "tgma.in",
    "thanksnospam.info", "thc.st", "thisisnotmyrealemail.com",
    "throwam.com", "throwaway.email",
    "throwb.com", "throwme.us",
    "tilien.com", "tmail.com", "tmailinator.com",
    "toiea.com", "toot.at",
    "top.ua", "topranklist.de", "tradermail.info",
    "trash-amil.com", "trash-mail.at", "trash-mail.com",
    "trash-mail.de", "trash-mail.ga", "trash-mail.io",
    "trash-mail.xyz", "trash2009.com", "trash2010.com",
    "trash2011.com", "trashemail.de", "trashimail.com",
    "trashmailer.com", "trashmail.at",
    "trashmail.com", "trashmail.io", "trashmail.me",
    "trashmail.net", "trashmail.org",
    "trashmail.xyz", "trashmailer.com",
    "trashspam.com", "treesurgery.net", "trickmail.net",
    "trillianpro.com", "trmailbox.com",
    "trollproject.com", "tryalert.com",
    "turual.com", "twinmail.de",
    "tyldd.com", "uggsrock.com",
    "umail.net", "unlimit.com",
    "unmail.ru", "uroid.com",
    "us.af", "uyhip.com",
    "venompen.com", "veryday.ch",
    "veryrealemail.com", "viditag.com",
    "viewcastmedia.com", "viewcastmedia.net", "viewcastmedia.org",
    "violinmakers.co.uk", "vomoto.com",
    "vpn.st", "vsimcard.com",
    "vubby.com", "walala.org",
    "walkmail.net", "walkmail.ru",
    "webemail.me", "weg-werf-email.de",
    "wegwerf-email.at", "wegwerf-email.de",
    "wegwerf-email.net", "wegwerf-email.org",
    "wegwerfadresse.de", "wegwerfemail.com",
    "wegwerfemail.de", "wegwerfemail.net",
    "wegwerfemail.org", "wegwerfmail.de",
    "wegwerfmail.info", "wegwerfmail.net",
    "wegwerfmail.org", "wetrainbayarea.com",
    "wetrainbayarea.org", "wh4f.org",
    "whatpaas.com", "whopy.com",
    "wilemail.com", "willhackforfood.biz",
    "willselfdestruct.com", "winemaven.info",
    "wronghead.com", "wuzup.net",
    "wuzupmail.net", "www.e4ward.com",
    "www.gishpuppy.com", "www.mailinator.com",
    "x.ip6.li", "xagloo.co", "xagloo.com",
    "xemaps.com", "xents.com", "xmaily.com",
    "xoxy.net", "xyzfree.net", "yapped.net",
    "yep.it", "yogamaven.com", "yopmail.com",
    "yopmail.fr", "yopmail.net", "youmail.ga",
    "yourdomain.com", "youremail.cf",
    "youremail.ga", "youremail.gq", "yourewrongit.com",
    "yuurok.com", "z1p.biz", "za.com",
    "zehnminutenmail.de", "zippymail.info",
    "zoemail.com", "zoemail.net", "zoemail.org",
    "zomg.info",
}


def is_disposable_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in DISPOSABLE_DOMAINS


# ---------------------------------------------------------------------------
# MX record check (verify domain can actually receive email)
# ---------------------------------------------------------------------------
def has_mx_record(email: str) -> bool:
    """Returns True if the email's domain has MX records (can receive mail)."""
    domain = email.rsplit("@", 1)[-1].lower()
    try:
        # Use getaddrinfo trick: if DNS resolves, domain probably exists.
        # Full MX check requires dnspython — use socket fallback here.
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False


try:
    import dns.resolver as _dns_resolver

    def has_mx_record(email: str) -> bool:  # noqa: F811 — override with real MX check
        domain = email.rsplit("@", 1)[-1].lower()
        try:
            _dns_resolver.resolve(domain, "MX")
            return True
        except Exception:
            return False

except ImportError:
    pass  # keep the socket-based fallback above


# ---------------------------------------------------------------------------
# Combined check
# ---------------------------------------------------------------------------
def validate_email_address(email: str) -> str | None:
    """
    Returns an error string if the email is invalid/blocked, or None if OK.
    """
    email = email.strip().lower()

    if not is_valid_email_format(email):
        return "Invalid email address format"

    if is_disposable_email(email):
        return "Disposable or temporary email addresses are not allowed"

    if not has_mx_record(email):
        return "Email domain does not appear to exist"

    return None
