import { USE_MOCK } from '../services/api.js'
import { listKnownTickers } from '../services/mocks/mockServer.js'

/**
 * Lista usada nas sugestões da busca (autocomplete).
 *
 * É uma lista fixa, guardada no próprio front-end: as APIs do projeto não têm
 * uma rota de "pesquisar ativos". Para sugerir um ativo novo, basta acrescentar
 * uma linha aqui. Ativos fora da lista continuam podendo ser buscados
 * normalmente, digitando o código inteiro.
 */
export const TICKERS = [
  // ----- B3: bancos e financeiro -----
  { ticker: 'ITUB4', name: 'Itaú Unibanco PN' },
  { ticker: 'ITUB3', name: 'Itaú Unibanco ON' },
  { ticker: 'BBDC4', name: 'Bradesco PN' },
  { ticker: 'BBDC3', name: 'Bradesco ON' },
  { ticker: 'BBAS3', name: 'Banco do Brasil ON' },
  { ticker: 'SANB11', name: 'Santander Brasil Unit' },
  { ticker: 'BPAC11', name: 'BTG Pactual Unit' },
  { ticker: 'ITSA4', name: 'Itaúsa PN' },
  { ticker: 'ITSA3', name: 'Itaúsa ON' },
  { ticker: 'B3SA3', name: 'B3 ON' },
  { ticker: 'BBSE3', name: 'BB Seguridade ON' },
  { ticker: 'CXSE3', name: 'Caixa Seguridade ON' },
  { ticker: 'PSSA3', name: 'Porto Seguro ON' },
  { ticker: 'IRBR3', name: 'IRB Brasil RE ON' },
  { ticker: 'BRSR6', name: 'Banrisul PNB' },
  { ticker: 'ABCB4', name: 'Banco ABC Brasil PN' },

  // ----- B3: petróleo, mineração e siderurgia -----
  { ticker: 'PETR4', name: 'Petrobras PN' },
  { ticker: 'PETR3', name: 'Petrobras ON' },
  { ticker: 'PRIO3', name: 'PRIO ON' },
  { ticker: 'BRAV3', name: 'Brava Energia ON' },
  { ticker: 'RECV3', name: 'PetroRecôncavo ON' },
  { ticker: 'VBBR3', name: 'Vibra Energia ON' },
  { ticker: 'UGPA3', name: 'Ultrapar ON' },
  { ticker: 'CSAN3', name: 'Cosan ON' },
  { ticker: 'RAIZ4', name: 'Raízen PN' },
  { ticker: 'VALE3', name: 'Vale ON' },
  { ticker: 'BRAP4', name: 'Bradespar PN' },
  { ticker: 'CMIN3', name: 'CSN Mineração ON' },
  { ticker: 'CSNA3', name: 'CSN ON' },
  { ticker: 'GGBR4', name: 'Gerdau PN' },
  { ticker: 'GOAU4', name: 'Metalúrgica Gerdau PN' },
  { ticker: 'USIM5', name: 'Usiminas PNA' },
  { ticker: 'BRKM5', name: 'Braskem PNA' },
  { ticker: 'UNIP6', name: 'Unipar PNB' },

  // ----- B3: energia, saneamento e telecom -----
  { ticker: 'EQTL3', name: 'Equatorial ON' },
  { ticker: 'CMIG4', name: 'Cemig PN' },
  { ticker: 'CPLE3', name: 'Copel ON' },
  { ticker: 'ENGI11', name: 'Energisa Unit' },
  { ticker: 'EGIE3', name: 'Engie Brasil ON' },
  { ticker: 'TAEE11', name: 'Taesa Unit' },
  { ticker: 'CPFE3', name: 'CPFL Energia ON' },
  { ticker: 'ENEV3', name: 'Eneva ON' },
  { ticker: 'AURE3', name: 'Auren Energia ON' },
  { ticker: 'SBSP3', name: 'Sabesp ON' },
  { ticker: 'SAPR11', name: 'Sanepar Unit' },
  { ticker: 'CSMG3', name: 'Copasa ON' },
  { ticker: 'VIVT3', name: 'Telefônica Brasil (Vivo) ON' },
  { ticker: 'TIMS3', name: 'TIM ON' },

  // ----- B3: consumo, varejo e saúde -----
  { ticker: 'ABEV3', name: 'Ambev ON' },
  { ticker: 'MGLU3', name: 'Magazine Luiza ON' },
  { ticker: 'LREN3', name: 'Lojas Renner ON' },
  { ticker: 'AZZA3', name: 'Azzas 2154 ON' },
  { ticker: 'ALPA4', name: 'Alpargatas PN' },
  { ticker: 'VIVA3', name: 'Vivara ON' },
  { ticker: 'GRND3', name: 'Grendene ON' },
  { ticker: 'ASAI3', name: 'Assaí ON' },
  { ticker: 'PCAR3', name: 'GPA (Pão de Açúcar) ON' },
  { ticker: 'MDIA3', name: 'M. Dias Branco ON' },
  { ticker: 'BEEF3', name: 'Minerva ON' },
  { ticker: 'SMTO3', name: 'São Martinho ON' },
  { ticker: 'SLCE3', name: 'SLC Agrícola ON' },
  { ticker: 'TTEN3', name: '3tentos ON' },
  { ticker: 'RADL3', name: 'RD Saúde (Raia Drogasil) ON' },
  { ticker: 'HAPV3', name: 'Hapvida ON' },
  { ticker: 'RDOR3', name: "Rede D'Or ON" },
  { ticker: 'FLRY3', name: 'Fleury ON' },
  { ticker: 'HYPE3', name: 'Hypera ON' },
  { ticker: 'QUAL3', name: 'Qualicorp ON' },
  { ticker: 'COGN3', name: 'Cogna ON' },
  { ticker: 'YDUQ3', name: 'Yduqs ON' },
  { ticker: 'CVCB3', name: 'CVC ON' },

  // ----- B3: indústria, transporte, construção e tecnologia -----
  { ticker: 'WEGE3', name: 'WEG ON' },
  { ticker: 'SUZB3', name: 'Suzano ON' },
  { ticker: 'KLBN11', name: 'Klabin Unit' },
  { ticker: 'DXCO3', name: 'Dexco ON' },
  { ticker: 'POMO4', name: 'Marcopolo PN' },
  { ticker: 'RAPT4', name: 'Randoncorp PN' },
  { ticker: 'TUPY3', name: 'Tupy ON' },
  { ticker: 'RENT3', name: 'Localiza ON' },
  { ticker: 'MOVI3', name: 'Movida ON' },
  { ticker: 'VAMO3', name: 'Vamos ON' },
  { ticker: 'SIMH3', name: 'Simpar ON' },
  { ticker: 'RAIL3', name: 'Rumo ON' },
  { ticker: 'ECOR3', name: 'Ecorodovias ON' },
  { ticker: 'MOTV3', name: 'Motiva ON' },
  { ticker: 'MULT3', name: 'Multiplan ON' },
  { ticker: 'IGTI11', name: 'Iguatemi Unit' },
  { ticker: 'ALOS3', name: 'Allos ON' },
  { ticker: 'CYRE3', name: 'Cyrela ON' },
  { ticker: 'MRVE3', name: 'MRV ON' },
  { ticker: 'EZTC3', name: 'EZTEC ON' },
  { ticker: 'DIRR3', name: 'Direcional ON' },
  { ticker: 'CURY3', name: 'Cury ON' },
  { ticker: 'TEND3', name: 'Tenda ON' },
  { ticker: 'TOTS3', name: 'Totvs ON' },
  { ticker: 'LWSA3', name: 'LWSA ON' },
  { ticker: 'INTB3', name: 'Intelbras ON' },

  // ----- B3: fundos de índice (ETFs) -----
  { ticker: 'BOVA11', name: 'iShares Ibovespa (ETF)' },
  { ticker: 'SMAL11', name: 'iShares Small Cap (ETF)' },
  { ticker: 'IVVB11', name: 'iShares S&P 500 (ETF)' },

  // ----- B3: fundos imobiliários (FIIs) -----
  // o "(FII)" no nome faz a busca por "fii" listar os fundos
  { ticker: 'MXRF11', name: 'Maxi Renda (FII)' },
  { ticker: 'KNRI11', name: 'Kinea Renda Imobiliária (FII)' },
  { ticker: 'KNCR11', name: 'Kinea Rendimentos Imobiliários (FII)' },
  { ticker: 'KNIP11', name: 'Kinea Índices de Preços (FII)' },
  { ticker: 'KNHF11', name: 'Kinea Hedge Fund (FII)' },
  { ticker: 'KNSC11', name: 'Kinea Securities (FII)' },
  { ticker: 'KNUQ11', name: 'Kinea Unique HY (FII)' },
  { ticker: 'KFOF11', name: 'Kinea FoF (FII)' },
  { ticker: 'HGLG11', name: 'Pátria Log (CSHG Logística) (FII)' },
  { ticker: 'HGRU11', name: 'Pátria Renda Urbana (CSHG) (FII)' },
  { ticker: 'HGBS11', name: 'Hedge Brasil Shopping (FII)' },
  { ticker: 'HGRE11', name: 'Pátria Escritórios (CSHG Real Estate) (FII)' },
  { ticker: 'HGCR11', name: 'Pátria Recebíveis (CSHG) (FII)' },
  { ticker: 'HFOF11', name: 'Hedge Top FOFII 3 (FII)' },
  { ticker: 'XPML11', name: 'XP Malls (FII)' },
  { ticker: 'XPLG11', name: 'XP Log (FII)' },
  { ticker: 'XPCI11', name: 'XP Crédito Imobiliário (FII)' },
  { ticker: 'XPSF11', name: 'XP Selection FoF (FII)' },
  { ticker: 'VISC11', name: 'Vinci Shopping Centers (FII)' },
  { ticker: 'VILG11', name: 'Vinci Logística (FII)' },
  { ticker: 'VINO11', name: 'Vinci Offices (FII)' },
  { ticker: 'BTLG11', name: 'BTG Pactual Logística (FII)' },
  { ticker: 'BTCI11', name: 'BTG Pactual Crédito Imobiliário (FII)' },
  { ticker: 'BTHF11', name: 'BTG Pactual Real Estate Hedge Fund (FII)' },
  { ticker: 'BRCR11', name: 'BTG Pactual Corporate Office Fund (FII)' },
  { ticker: 'BRCO11', name: 'Bresco Logística (FII)' },
  { ticker: 'LVBI11', name: 'VBI Logístico (FII)' },
  { ticker: 'PVBI11', name: 'VBI Prime Properties (FII)' },
  { ticker: 'CVBI11', name: 'VBI CRI (FII)' },
  { ticker: 'GGRC11', name: 'GGR Covepi Renda (FII)' },
  { ticker: 'TRXF11', name: 'TRX Real Estate (FII)' },
  { ticker: 'ALZR11', name: 'Alianza Trust Renda Imobiliária (FII)' },
  { ticker: 'HSML11', name: 'HSI Malls (FII)' },
  { ticker: 'IRDM11', name: 'Iridium Recebíveis (FII)' },
  { ticker: 'CPTS11', name: 'Capitânia Securities II (FII)' },
  { ticker: 'RECR11', name: 'REC Recebíveis (FII)' },
  { ticker: 'RBRR11', name: 'RBR Rendimento High Grade (FII)' },
  { ticker: 'RBRF11', name: 'RBR Alpha Multiestratégia (FII)' },
  { ticker: 'RBRP11', name: 'RBR Properties (FII)' },
  { ticker: 'MCCI11', name: 'Mauá Capital Recebíveis (FII)' },
  { ticker: 'VGIR11', name: 'Valora RE III (FII)' },
  { ticker: 'VGHF11', name: 'Valora Hedge Fund (FII)' },
  { ticker: 'JSRE11', name: 'JS Real Estate Multigestão (FII)' },
  { ticker: 'RBVA11', name: 'Rio Bravo Renda Varejo (FII)' },
  { ticker: 'TVRI11', name: 'Tivio Renda Imobiliária (FII)' },
  { ticker: 'VRTA11', name: 'Fator Verita (FII)' },
  { ticker: 'RZTR11', name: 'Riza Terrax (FII)' },
  { ticker: 'RZAK11', name: 'Riza Akin (FII)' },
  { ticker: 'SNCI11', name: 'Suno Recebíveis Imobiliários (FII)' },
  { ticker: 'TGAR11', name: 'TG Ativo Real (FII)' },
  { ticker: 'URPR11', name: 'Urca Prime Renda (FII)' },
  { ticker: 'HABT11', name: 'Habitat Recebíveis (FII)' },
  { ticker: 'HCTR11', name: 'Hectare CE (FII)' },
  { ticker: 'DEVA11', name: 'Devant Recebíveis (FII)' },
  { ticker: 'VCJR11', name: 'Vectis Juros Real (FII)' },
  { ticker: 'AFHI11', name: 'AF Invest CRI (FII)' },
  { ticker: 'CLIN11', name: 'Clave Índices de Preços (FII)' },
  { ticker: 'MFII11', name: 'Mérito Desenvolvimento Imobiliário (FII)' },
  { ticker: 'OUJP11', name: 'Ourinvest JPP (FII)' },
  { ticker: 'WHGR11', name: 'WHG Real Estate (FII)' },
  { ticker: 'GARE11', name: 'Guardian Real Estate (FII)' },

  // ----- Estados Unidos -----
  { ticker: 'AAPL', name: 'Apple' },
  { ticker: 'MSFT', name: 'Microsoft' },
  { ticker: 'NVDA', name: 'NVIDIA' },
  { ticker: 'GOOGL', name: 'Alphabet (Google)' },
  { ticker: 'AMZN', name: 'Amazon' },
  { ticker: 'META', name: 'Meta Platforms' },
  { ticker: 'TSLA', name: 'Tesla' },
  { ticker: 'NFLX', name: 'Netflix' },
  { ticker: 'AMD', name: 'AMD' },
  { ticker: 'INTC', name: 'Intel' },
  { ticker: 'DIS', name: 'Walt Disney' },
  { ticker: 'KO', name: 'Coca-Cola' },
  { ticker: 'NKE', name: 'Nike' },
  { ticker: 'JPM', name: 'JPMorgan Chase' },
  { ticker: 'MELI', name: 'Mercado Livre' },
  { ticker: 'NU', name: 'Nubank (Nu Holdings)' },
]

// "Itaú" -> "ITAU": ignora acentos e maiúsculas na comparação
function normalize(text) {
  return String(text)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
}

// No modo mock só existem alguns ativos; sugerir os outros levaria a "não encontrado"
function availableTickers() {
  if (!USE_MOCK) return TICKERS
  const known = new Set(listKnownTickers())
  return TICKERS.filter((t) => known.has(t.ticker))
}

/**
 * Sugestões para o texto digitado, na ordem:
 * 1) código começa com o texto ("BBA" -> BBAS3)
 * 2) código contém o texto
 * 3) nome da empresa contém o texto ("banco" -> BBAS3)
 */
export function suggestTickers(query, limit = 6) {
  const q = normalize(query).trim()
  if (!q) return []

  const starts = []
  const contains = []
  const byName = []
  for (const item of availableTickers()) {
    if (item.ticker.startsWith(q)) starts.push(item)
    else if (item.ticker.includes(q)) contains.push(item)
    else if (normalize(item.name).includes(q)) byName.push(item)
  }
  return [...starts, ...contains, ...byName].slice(0, limit)
}
