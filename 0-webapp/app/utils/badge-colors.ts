// Government theme colors for professional appearance
export const GOV_COLORS = [
  "govGray",
  "govRed",
  "govAmber",
  "govGreen",
  "govBlue",
];

export const COLORS = [
  "gray",
  "red",
  "pink",
  "grape",
  "violet",
  "indigo",
  "blue",
  "cyan",
  "teal",
  "green",
  "lime",
  "yellow",
  "orange",
];

export const TAGS = [
  "Europese zaken",
  "Onbekend",
  "afval",
  "arbeidsomstandigheden",
  "arbeidsongeschiktheid en werkloosheid",
  "arbeidsverhoudingen",
  "basisonderwijs",
  "begroting",
  "belasting",
  "beroepsonderwijs",
  "bestuursrecht",
  "bezwaar en klachten",
  "bodem",
  "bouwen en verbouwen",
  "criminaliteit",
  "cultureel erfgoed",
  "cultuur",
  "cultuur en recreatie",
  "defensie",
  "dienstensector",
  "economie",
  "energie",
  "ethiek",
  "geluid",
  "geneesmiddelen en medische hulpmiddelen",
  "gezin en kinderen",
  "gezondheidsrisico's",
  "handel",
  "hoger onderwijs",
  "informatievoorziening en ICT",
  "inrichting van de overheid",
  "integratie",
  "internationaal",
  "internationale betrekkingen",
  "jeugdzorg",
  "kenniseconomie",
  "klimaatverandering",
  "koninkrijksrelaties",
  "landbouw, visserij, voedselkwaliteit",
  "lucht",
  "luchtvaart",
  "markttoezicht",
  "media",
  "migratie",
  "migratie en integratie",
  "natuur en milieu",
  "natuuren landschapsbeheer",
  "netwerken",
  "ondernemen",
  "onderwijs en wetenschap",
  "onderzoek en wetenschap",
  "ontwikkelingssamenwerking",
  "openbaar vervoer",
  "openbare orde en veiligheid",
  "organisatie en bedrijfsvoering",
  "ouderen",
  "overheidsfinanciën",
  "privaatrecht",
  "railen wegverkeer",
  "rechten en vrijheden",
  "rechtspraak",
  "recreatie",
  "religie",
  "ruimte en infrastructuur",
  "ruimtelijke ordening",
  "staatsrecht",
  "stoffen",
  "strafrecht",
  "terrorisme",
  "transport",
  "veiligheid",
  "verkeer",
  "voortgezet onderwijs",
  "water",
  "waterbeheer",
  "werk",
  "wonen",
  "woningmarkt",
  "ziekten en behandelingen",
  "zorg en gezondheid",
  "zorgverzekeringen",
];

export default function getBadgeColor(tag: string): { from: string; to: string; deg: number } {
  switch (tag) {
    // European and international affairs
    case "Europese zaken":
      return { from: "govBlue", to: "govBlue", deg: 90 };
    case "internationaal":
    case "internationale betrekkingen":
    case "koninkrijksrelaties":
    case "ontwikkelingssamenwerking":
      return { from: "govBlue", to: "govBlue", deg: 90 };
    
    // Unknown/General
    case "Onbekend":
      return { from: "govGray", to: "govGray", deg: 90 };
    
    // Environment and sustainability
    case "afval":
    case "natuur en milieu":
    case "natuuren landschapsbeheer":
    case "klimaatverandering":
    case "bodem":
    case "water":
    case "waterbeheer":
    case "lucht":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Labor and employment
    case "arbeidsomstandigheden":
    case "arbeidsongeschiktheid en werkloosheid":
    case "arbeidsverhoudingen":
    case "werk":
      return { from: "govAmber", to: "govAmber", deg: 90 };
    
    // Education
    case "basisonderwijs":
    case "beroepsonderwijs":
    case "hoger onderwijs":
    case "voortgezet onderwijs":
    case "onderwijs en wetenschap":
    case "onderzoek en wetenschap":
      return { from: "govBlue", to: "govBlue", deg: 90 };
    
    // Finance and budget
    case "begroting":
    case "belasting":
    case "overheidsfinanciën":
    case "economie":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Legal and administrative
    case "bestuursrecht":
    case "staatsrecht":
    case "privaatrecht":
    case "strafrecht":
    case "rechtspraak":
    case "rechten en vrijheden":
      return { from: "govGray", to: "govGray", deg: 90 };
    
    // Government organization
    case "inrichting van de overheid":
    case "organisatie en bedrijfsvoering":
      return { from: "govBlue", to: "govBlue", deg: 90 };
    
    // Security and safety
    case "defensie":
    case "openbare orde en veiligheid":
    case "veiligheid":
    case "terrorisme":
    case "criminaliteit":
      return { from: "govRed", to: "govRed", deg: 90 };
    
    // Health and care
    case "geneesmiddelen en medische hulpmiddelen":
    case "gezondheidsrisico's":
    case "ziekten en behandelingen":
    case "zorg en gezondheid":
    case "zorgverzekeringen":
    case "jeugdzorg":
      return { from: "govRed", to: "govRed", deg: 90 };
    
    // Social affairs
    case "gezin en kinderen":
    case "ouderen":
    case "integratie":
    case "migratie":
    case "migratie en integratie":
      return { from: "govAmber", to: "govAmber", deg: 90 };
    
    // Infrastructure and transport
    case "transport":
    case "openbaar vervoer":
    case "railen wegverkeer":
    case "verkeer":
    case "luchtvaart":
    case "ruimte en infrastructuur":
    case "ruimtelijke ordening":
      return { from: "govAmber", to: "govAmber", deg: 90 };
    
    // Energy and utilities
    case "energie":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Technology and communication
    case "informatievoorziening en ICT":
    case "netwerken":
    case "media":
      return { from: "govBlue", to: "govBlue", deg: 90 };
    
    // Culture and recreation
    case "cultureel erfgoed":
    case "cultuur":
    case "cultuur en recreatie":
    case "recreatie":
      return { from: "govGray", to: "govGray", deg: 90 };
    
    // Housing and urban development
    case "bouwen en verbouwen":
    case "wonen":
    case "woningmarkt":
      return { from: "govAmber", to: "govAmber", deg: 90 };
    
    // Business and commerce
    case "dienstensector":
    case "handel":
    case "ondernemen":
    case "kenniseconomie":
    case "markttoezicht":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Agriculture and food
    case "landbouw, visserij, voedselkwaliteit":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Ethics and religion
    case "ethiek":
    case "religie":
      return { from: "govGray", to: "govGray", deg: 90 };
    
    // Sound and environment
    case "geluid":
    case "stoffen":
      return { from: "govGreen", to: "govGreen", deg: 90 };
    
    // Complaints and procedures
    case "bezwaar en klachten":
      return { from: "govRed", to: "govRed", deg: 90 };
    
    default:
      return { from: "govGray", to: "govBlue", deg: 90 };
  }
}
