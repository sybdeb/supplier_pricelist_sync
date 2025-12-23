# Skip Voorwaarden - Gebruikershandleiding

## Overzicht

Vanaf nu kun je per leverancier configureren welke producten **overgeslagen** worden tijdens import. Dit voorkomt dat je database vol komt te staan met:
- Producten zonder voorraad
- Producten met prijs €0
- Discontinued/EOL producten
- Onvolledige product data

## Configuratie

### 1. Mapping Template Openen

Navigeer naar: **Supplier Pricelist Sync → Configuration → Mapping Templates**

Selecteer of maak een template voor je leverancier.

### 2. Tab "Skip Voorwaarden"

Hier configureer je de filters:

#### **Voorraad Filters**

- **Skip als Voorraad = 0**: Schakel aan om producten zonder voorraad te negeren
- **Minimum Voorraad**: Stel drempelwaarde in (bijv. 10 = skip alles onder 10 stuks)

#### **Prijs Filters**

- **Skip als Prijs = 0**: Standaard AAN - skip producten zonder prijs
- **Minimum Prijs**: Skip producten onder bepaald bedrag (bijv. €1,00)

#### **Overige Filters**

- **Skip Discontinued**: Skip producten gemarkeerd als "discontinued" of "EOL" in CSV
- **Verplichte Velden**: Komma-gescheiden lijst van CSV kolommen die ingevuld MOETEN zijn
  - Voorbeeld: `ean,price,stock`
  - Als één van deze velden leeg is → skip

## Gebruik tijdens Import

1. **Direct Import Wizard** openen
2. **Leverancier** selecteren
3. **Template** selecteren (optioneel - wordt automatisch geladen voor deze leverancier)
4. Je ziet een **popup** met de actieve skip-voorwaarden
5. CSV uploaden en **Parse & Map**
6. **Execute Import**

## Import Summary

Na de import zie je in de summary:

```
📊 Statistieken:
  Totaal rijen: 1000
  ✅ Aangemaakt: 450
  🔄 Bijgewerkt: 300
  ⏭️  Overgeslagen: 250

ℹ️  Skip redenen:
  - Geen voorraad: 150x
  - Prijs te laag (< 5.0): 50x
  - Verplicht veld 'ean' ontbreekt: 30x
  - Product discontinued: 20x
```

## Voorbeelden

### Voorbeeld 1: Alleen producten met voorraad

```
✓ Skip als Voorraad = 0
  Min voorraad: 0
```

→ Importeert alleen producten met stock > 0

### Voorbeeld 2: B2B leverancier (minimale afname 10 stuks)

```
✓ Skip als Voorraad = 0
  Min voorraad: 10
✓ Skip als Prijs = 0
  Min prijs: 0.0
```

→ Importeert alleen producten met ≥ 10 stuks voorraad

### Voorbeeld 3: Premium producten (min €5)

```
✓ Skip als Voorraad = 0
✓ Skip als Prijs = 0
  Min prijs: 5.00
```

→ Importeert alleen producten ≥ €5,00

### Voorbeeld 4: Volledige data verplicht

```
✓ Skip als Voorraad = 0
✓ Skip als Prijs = 0
  Verplichte velden: ean,price,stock,brand
```

→ Skip rijen zonder EAN, prijs, voorraad OF merk

## Technische Details

### Voorraad detectie

Het systeem zoekt naar voorraad in deze velden (in volgorde):
1. `qty_available` (Odoo standaard)
2. `stock` (CSV kolom gemapped als "stock")
3. Anders: 0

### Discontinued detectie

Het systeem zoekt naar kolommen met:
- `discontinued` in de naam
- `eol` in de naam

Waarden die als "discontinued" worden gezien:
- `true`, `1`, `yes`, `ja`, `discontinued`

### Verplichte velden check

- Case-sensitive match met CSV kolom namen
- Lege strings worden als "ontbreekt" gezien
- Meerdere velden: komma-gescheiden, spaties worden genegeerd

## Tips

1. **Test eerst zonder filters**: Doe een import zonder skip-voorwaarden om te zien wat er in de CSV staat
2. **Check de summary**: Kijk naar de skip redenen om filters af te stellen
3. **Template hergebruik**: Eenmaal ingesteld, wordt de template automatisch geladen
4. **Combineer filters**: Je kunt meerdere voorwaarden tegelijk gebruiken

## FAQ

**Q: Wat gebeurt er met producten die al bestaan maar nu geskipped worden?**
A: Ze blijven ongewijzigd in de database. De import raakt ze niet aan.

**Q: Kan ik tijdelijk filters uitschakelen?**
A: Ja, kies "Geen template" in de wizard of maak een nieuwe template zonder filters.

**Q: Worden geskipte rijen geteld als errors?**
A: Nee, ze worden geteld als "overgeslagen" (skipped), niet als errors.

**Q: Kan ik per import andere filters gebruiken?**
A: Ja, selecteer een ander template of maak meerdere templates voor dezelfde leverancier.

**Q: Hoe weet ik welke kolom "stock" is?**
A: Kijk in de mapping - het veld gemapped naar "supplierinfo.qty_available" of "stock" wordt gebruikt.
