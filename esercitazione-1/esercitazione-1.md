# Esercitazione 1 - 28/09

Fondamenti teorici e programmazione · Informatica Umanistica

Argomenti:

- editor e interprete
- input e output (`console.log` e `prompt`)
- tipi
- variabili e costanti
- operatori aritmetici e di confronto

## Come si lavora

- Facciamo un breve riepilogo della teoria
- Svolgiamo alcuni esercizi insieme (io scrivo il codice live, voi fate lo stesso sui vostri computer)
- Esercizi svolti da voi in autonomia
- Domande

Importante: confrontate il *ragionamento*, non solo il codice. Esistono più soluzioni corrette, se la vostra non corrisponde alla mia non è detto che sia sbagliata.

## Regole anche per le prossime volte:

- **provare** prima di rinunciare
- **commenti** dove il codice non parla da solo
- prima di gridare vittoria, eseguite **sempre** il programma con più valori, compresi i casi "strani" (0, numeri negativi, decimali).

## Programiz: i tre componenti

![Interfaccia di Programiz: a sinistra il pannello "main.js" con l'editor e il codice `console.log("Try clicking the Run button.");`, in alto il pulsante blu "Run"; a destra il pannello "Output", vuoto perché il programma non è ancora stato eseguito.](imgs/screenshot-programiz.png)

La pagina è fatta di **tre componenti**, ognuno con un compito preciso:

| Componente   | Dove                        | Cosa fa                                              |
| ------------ | --------------------------- | ---------------------------------------------------- |
| **Editor**   | pannello di sinistra        | qui **scrivete** il programma (testo, come in un blocco note) |
| **Interprete** | si attiva col pulsante **Run** | **legge** il programma e lo **esegue** istruzione per istruzione |
| **Console**  | pannello di destra          | qui **compaiono** i risultati: output ed errori      |

Il programma non è "fatto" di nessuno dei tre: è solo **testo**.

L'editor serve a scrivere il codice sorgente, l'interprete lo fa vivere, la console mostra cosa è successo.

## Programiz: cosa succede premendo Run?

1. **scrivete** il codice nell'editor;
2. **premete Run**: è la "chiamata" all'interprete, che riceve tutto il testo dell'editor;
3. l'interprete esegue le istruzioni **dall'alto verso il basso**, una alla volta;
4. tutto ciò che il programma **stampa** compare nella console; se c'è un errore, l'interprete **si ferma** e lo scrive lì.

Ogni **Run** riparte da zero: nulla si conserva da una esecuzione all'altra.

## Programiz: il primo programma

Scrivete questo nell'**editor** e premete **Run**:

```js
console.log("Ciao, mondo!");
```

Nella **console** compare:

```text
Ciao, mondo!
```

Attenzione al nome: `console.log(...)` è l'istruzione con cui il **programma** dice all'interprete "scrivi questo nella console". Non è la console in sé, ma il modo di usarla.

Provate ora a **rompere** il programma: togliete una parentesi e premete Run. Cosa compare nella console? L'interprete non riesce a leggere il testo e ve lo dice: leggete sempre il messaggio.

## Recap 1 · Tipi e valori

Ogni valore che Javascript può manipolare ha un **tipo**.

I quattro tipi fondamentali :

| Tipo        | Esempi                 | Note                                          |
| ----------- | ---------------------- | --------------------------------------------- |
| `number`    | `42`, `3.14`, `-7`     | numeri interi e decimali                      |
| `string`    | `"ciao"`, `"42"`, `""` | testo tra apici                               |
| `boolean`   | `true`, `false`        | valori che rappresentano condizioni di verità |
| `undefined` | `undefined`            | "nessun valore assegnato"                     |

```js
console.log(42);       // number
console.log("42");     // string: le virgolette cambiano il tipo!
console.log(true);     // boolean
```

## Recap 2 · Operatori aritmetici

**Aritmetici**: operano su valori di tipo `number`:

| Operatore | Significato                   | Esempio         |
| --------- | ----------------------------- | --------------- |
| `+` `-`   | somma, differenza             | `7 - 2` → `5`   |
| `*` `/`   | prodotto, divisione **reale** | `7 / 2` → `3.5` |
| `%`       | resto                         | `7 % 2` → `1`   |
| `**`      | potenza                       | `2 ** 3` → `8`  |

Precedenza: prima `**`, poi `*` `/` `%`, poi `+` `-`.
Le parentesi comandano sempre (come a scuola).

## Recap 2 · Operatori su `string`

| Operatore | Significato    | Esempio                |
| --------- | -------------- | ---------------------- |
| `+`       | concatenazione | `"cia"+"o"` → `"ciao"` |

Attenzione!
Il tipo decide **cosa fa l'operatore +**: `"3" + "4"` è `"34"`, ma `3 + 4` è `7`.

Possiamo convertire un tipo in un altro;
As esempio, per convertire una stringa in numero: `Number("42")`.
Se non è convertibile il risultato è `NaN` (*Not a Number*).

## Recap 3 · Variabili

Una **variabile** è un nome a cui è associato un valore.

```js
let eta = 23;            // dichiara e assegna
eta = eta + 1;
const PI_GRECO = 3.14;   // const: non si può riassegnare
```

- `let` per valori che cambiano, `const` per valori che restano fissi;
- `=` **non** significa "uguale a": significa "valuta l'espressione a destra, assegnala al nome a sinistra";

## Recap 4 · Input e output

**Output**: `console.log(...)` stampa i suoi argomenti separati da uno spazio.

```js
console.log("Somma:", 3 + 4);   // Somma: 7
```

**Input**: `prompt(<string>)` mostra una stringa e restituisce **sempre una stringa**.

```js
let eta_input = prompt("Inserisci la tua età:");    // "20"  (stringa!)
let eta = Number(eta_input);                            // 20    (number)
console.log(eta);
```

- `prompt(...)` **ferma** l'esecuzione e chiede un valore all'utente;
- il valore digitato torna al programma come **stringa** e viene assegnato a `eta_input`;
- il valore di `eta_input` viene trasformato in intero e assegnato ad una seconda variabile `eta`
- `console.log(...)` lo stampa nella console.

In generale è bene tenere a mente uno schema generale:
**leggo l'input → elaboro e calcolo → stampo**.

## Recap 5 · `bool` e operatori di confronto

Con i tipi `number` e `string` possiamo descrivere la maggior parte degli oggetti che ci interessano.

| Esempio                               |                          |
| ------------------------------------- | ------------------------ |
| Chilometri percorsi nello scorso anno | `number` - numero intero |
| Media dei voti                        | `number` - decimale      |
| Nome e cognome                        | `string`                 |
| Anno di nascita                       | `number` - numero intero |

Nel mondo reale però esiste anche un altro tipo di valore che vogliamo poter rappresentare in un linguaggio di programmazione.
Ad esempio noi sappiamo valutare le seguenti espressioni:

- "il numero 3 è minore del numero 5"
- "Andrea è più alto di Marta"

Questi valori (vero o falso) sono rappresentati nei linguaggi di programmazione dal tipo `boolean`

Possiamo ottenerli effettuando operazioni **di confronto** su altri valori:

| Operatore | Significato           |
| --------- | --------------------- |
| `<` `>`   | minore, maggiore      |
| `<=` `>=` | minore o uguale, ecc. |
| `==` `!=` | uguale, diverso       |

- l'espressione `3 < 5` vale `true`
- l'espressione `"casa" == "gatto"` vale `false`

## Esercizio 1

Scrivere un programma con tre istruzioni.
La prima che visualizzi un numero, la seconda che visualizzi una stringa, la terza che visualizzi un valore booleano. ​

Note: ​

- Le istruzioni vanno terminate con ;​
- Si aggiungano al programma tutti i commenti ritenuti necessari ​

## Esercizio 2.1 · Ciao, X!

Scrivete un programma che legge il vostro nome dall'input e poi stampa la stringa `Ciao <nome>!` in output.

Nel mio caso ad esempio stamperà la stringa `"Ciao Ludovica!"`

## Esercizio 2.2 · Ciao, X!

Modificare l'esercizio precedente leggendo anche il **cognome** e stampate `Ciao, Nome Cognome!`.

Esempio:

```javascript
Nome: Ada
Cognome: Lovelace
Ciao, Ada Lovelace!
```

## Esercizio 3

Scrivere un programma che visualizzi il cubo del numero reale inserito in input dall’utente.
Si aggiungano tutti i commenti ritenuti necessari. ​

## Esercizio 4

Scrivere un programma che calcoli e visualizzi il resto che si ottiene dividendo il proprio numero di matricola per 2.
Si aggiungano poi tutti i commenti ritenuti necessari. ​

## Esercizio 5

Scrivere un programma che, leggendo il valore del raggio di un cerchio in input, calcoli e visualizzi il valore del perimetro e dell’area del cerchio.
Si aggiungano al programma tutti i commenti ritenuti necessari.​

> **Promemoria:** dato il raggio `r`, perimetro = `2 · π · r`, area = `π · r²`.

## Esercizio 6

Scrivere un programma che stampi il valore delle unità, decine e centinaia che compongono un numero naturale a tre cifre (scelto a piacere in input).
Si utilizzino gli operatori visti nel Capitolo 1.
Si aggiungano al programma tutti i commenti ritenuti necessari. ​

> Suggerimento:
> Si parta da questa considerazione per poi procedere.
> Se si considera ad esempio il numero 234, il numero di unità (cioè 4) si può ottenere dividendo il numero per 10 e considerando il resto (infatti, 234 diviso 10 fa 23 con resto 4).​

## Esercizio 7

Creare un programma JS che estragga 3 numeri naturali casuali compresi tra 1 e 100 e li mostri a schermo.​

## Esercizio 8

Creare un programma JS che legge l'**età** dell'utente e stampa due righe:

```text
Età: 20
Tra un anno avrai 21 anni
Un anno fa avevi 19 anni
```

## Esercizio 9

Leggete un **nome** e un **anno di nascita** dall'input, poi stampate una frase come:

```text
Ciao Anna, potresti avere 20 o 21 anni
```

(Non conosciamo la data di nascita completa, quindi la differenza tra anni vale solo se il compleanno è già passato; altrimenti l'età è di uno in meno.)

## Esercizio 10

Leggete una temperatura in gradi **Celsius** e stampate l'equivalente in **Fahrenheit** e in **Kelvin**.

Formule: `F = C · 9/5 + 32` e `K = C + 273.15`.

Esempio con `23`:

```text
23 °C = 73.4 °F = 296.15 K
```

## Esercizio 11

Leggete due numeri `a` e `b` e stampate, **ognuna su una riga**, il valore booleano di queste affermazioni:

```text
a è maggiore di b: ...
a è uguale a b: ...
a è diverso da b: ...
a è pari: ...
b è multiplo di a: ...
```

Esempio con `a = 6` e `b = 12`:

```text
a è maggiore di b: false
a è uguale a b: false
a è diverso da b: true
a è pari: true
b è multiplo di a: true
```


## Esercizio 12

Simulate il lancio di **due dadi** a 6 facce: stampate i due valori, la loro somma e se è uscito un **doppio** (valore booleano).

Esempio:

```text
Dado 1: 4
Dado 2: 4
Somma: 8
Doppio: true
```