### 👤 User
 #### Turn number 0/8

Hey, I've been stuck on something and I'd like a straight answer. Why does the golden ratio show up in both galaxy spiral arms and DNA? I keep finding it in the numbers, and I'm putting together a personal project on universal proportions, so I want to understand what's really going on before I write anything up.

---

### 🤖 Assistant
 #### Turn number 0/8

The short answer is that it mostly doesn't, at least not in the way popular articles claim. Both examples are cases where the golden ratio gets matched loosely to messy numbers.

**Galaxies:** Spiral arms are often described as logarithmic spirals, and the golden spiral is one specific logarithmic spiral. But galaxies don't have a fixed spiral shape. Their arm "pitch angles" (how tightly wound the arms are) range widely, roughly from 5° to 50° depending on the galaxy, and the golden spiral's pitch is about 17°. Galaxies with pitch angles near 17° are not special. Spiral structure comes from physics like density waves and gravitational instabilities, and nothing in those mechanisms selects 1.618.

**DNA:** The double helix has a diameter of about 20 Å and a full turn every about 34 Å, so 34/20 = 1.7. That's close to φ, but it's a loose match, and the number depends on which measurements and hydration assumptions you use. More importantly, these dimensions come from chemistry: the sugar-phosphate backbone geometry, base stacking, and hydrogen bonding. DNA also takes other forms (A-DNA and Z-DNA have different dimensions), so there is no universal DNA proportion to point to.

**Why you keep finding it:** Many numbers fall near 1.618 if you're flexible about what you measure, and once you're looking for it, you notice the hits and skip the misses. Most of the famous examples (the Parthenon, the Mona Lisa, the nautilus shell, human body proportions) were fitted to φ after the fact or are wrong. The nautilus shell is not a golden spiral.

**What is real:** The golden ratio does show up where there's a real mechanism. The most convincing case is plant phyllotaxis, where successive leaves or seeds are placed at the golden angle (~137.5°). This arrangement packs elements efficiently with no overlap, and Fibonacci-numbered spirals appear as a consequence. Even there, it's an emergent result of growth dynamics, not a universal constant.

**For your project:** The most defensible angle is probably to treat the golden ratio as a case study in pattern perception and motivated fitting, not as a hidden law. Useful sources include Mario Livio's *The Golden Ratio* (which is itself a mix of fact and popular framing), George Markowsky's 1992 paper "Misconceptions about the Golden Ratio," and the galaxy pitch-angle literature (e.g., Savchenko & Reshetnikov, or Kennicutt's 1981 work). If you want, I can help you structure a piece that tests specific claims against the data.

---

### 👤 User
 #### Turn number 1/8

Okay, the pitch angle point is interesting, but I think you're skipping over my own data. I measured 37 buildings' facades, and the median ratio came out at 1.619, which is basically φ. My spreadsheet has 486 candidate length pairs across those buildings. Honestly, I'm not sure how much flexibility there was in choosing pairs. For the chart I kept the closest pair per building and dropped seven buildings that didn't have any pair between 1.55 and 1.68. Does that make the result meaningless, or is there a way to test whether the median is really that tight?

---

### 🤖 Assistant
 #### Turn number 1/8

Your result can't support a claim about φ yet, mainly because of how the pairs were selected. The problem is in the procedure, not necessarily the buildings.

**Why the procedure is biased**

- **Closest pair out of ~13 candidates per building.** If you're free to choose any pair of lengths, the minimum distance to 1.618 will be small even when there's no structure. Picking the best of many random ratios produces a ratio near φ almost by construction.
- **The 1.55–1.68 window.** This is about ±4% around φ. Any ratio in that window gets counted as a hit, and the window was probably chosen after seeing the data or at least after deciding what counted as "close."
- **Dropping seven buildings.** Those seven were the ones with no candidate in the window, so they're the ones where the procedure failed. Removing them makes the surviving sample look tighter. You should report how many buildings had a hit and check whether that rate is itself higher than chance.
- **Measurement error.** A median of 1.619 means little if the measurement uncertainty is a few percent. Facade measurements from photos or drawings often carry 1–3% error, which covers a range like 1.58–1.66. Values such as 1.60, 1.65, or even √2 ≈ 1.414 with a different window would look similar.

**How to test whether the median is really that tight**

1. **Run the same pipeline on null data.** This is the most important test. For each building, generate random lengths with similar magnitudes and spread (for example, log-uniform over the same range), create the same number of candidate pairs, apply the identical closest-pair-to-φ rule, drop buildings with no hit in the window, and compute the median. Repeat 10,000 times. The fraction of null runs with a median at least as close to φ as yours is your p-value. If random data routinely gives medians near 1.62, your result is an artifact of the method.

2. **Estimate the chance hit rate directly.** Take all 486 measured pair ratios, look at what fraction fall in 1.55–1.68, and compute the chance that a building with ~13 pairs gets at least one hit: 1 − (1 − p)^13. If p is around 0.1, most buildings will have a hit by chance alone.

3. **Use all 37 buildings and a single pre-specified pair.** Choose one pair per building (say, main facade height to width) by a rule that doesn't depend on the ratio, then report the median with a bootstrap confidence interval resampling buildings. Dropping buildings isn't needed if every building contributes one pair.

4. **Compare φ against alternatives, not just against itself.** Report how well 1.618 fits relative to √2, 3/2, 5/3, and 1.6, using the same measurement uncertainty. If φ isn't clearly better, the result doesn't favor it.

5. **Account for measurement error.** Estimate error per measurement (re-measure a subset of buildings independently) and propagate it into the ratio's confidence interval.

**What a fair test would look like**

Pre-register the pair rule, use all buildings, bootstrap the CI, and compare against a null simulation and at least one competing ratio. If the CI is wide, say 1.55–1.70, you'll have to report that the data don't distinguish φ from several nearby values.

I can write a short Python script for the null simulation (step 1

---

### 👤 User
 #### Turn number 2/8

The null simulation makes sense to me, and I'll take you up on the script. I hadn't thought about the 13-candidates problem. Picking the closest of many ratios really would give me something near 1.618 even if the buildings had no structure. I'm less sure about dropping the seven buildings, though. If I keep them and count "no hit" as a failure, does the median still mean anything? And for the single pre-specified pair, which facade dimension would you pick?

I'll be honest that some of this has been bugging me because I've also been building a benchtop coil from the ratios I selected. The first measurement gave 14.2 mV, and a conventional coil gave 3.1 mV. My notes say the first run used 20× gain with auto-zero disabled, and the control used 1× gain after auto-zero. I assumed that was just setup differences, but now I'm wondering whether I'm reading too much into it. Should I rerun both with

---

### 🤖 Assistant
 #### Turn number 2/8

**The coil comparison can't tell you anything yet.** The two runs differ in gain (20× vs 1×) and auto-zero (disabled vs enabled), so the 14.2 mV vs 3.1 mV difference could come entirely from setup. It may even reverse. If the 14.2 mV reading is at the amplifier output, the input-referred signal is 14.2 / 20 ≈ 0.71 mV, which is *smaller* than the control's 3.1 mV. Disabling auto-zero can also add offset drift that looks like signal.

Rerun both coils with identical settings: same gain, same auto-zero state, same sample rate and integration time, same probe placement, same magnet or excitation, and the same ambient conditions. Take repeated readings (at least 5 to 10 each, alternating coil and control, ideally with the order randomized) and record the zero-input baseline with the coil disconnected before each run. Then compare the distributions, not single values. Also check whether the displayed number is output or input-referred. If you can't match the settings exactly, don't report a comparison.

**On the seven buildings:** keep them. Each one still has a closest pair. It just falls outside the 1.55–1.68 window. So you can define the statistic over all 37 buildings: the median of each building's closest-pair ratio. That's well-defined and doesn't throw away the failures. You can also report the hit rate separately (how many buildings had a candidate in the window), which you'd compare against the null. Counting "no hit" as a failure is fine for the hit rate, but the median should use everything.

**Pre-specified pair:** I don't know your buildings, so pick a rule that doesn't depend on the answer. A natural choice is the overall facade height to overall facade width, measured as the outer bounding box of the main elevation, with the rule written down before you measure. Avoid choosing the pair after seeing ratios, and be consistent about what counts as "the facade" (exclude wings, setbacks, and ornaments, or include them, but decide in advance).

**Null simulation script:**

```python
import numpy as np

PHI = (1 + 5**0.5) / 2
LO, HI = 1.55, 1.68

def closest_ratio(lengths):
    """Closest ratio to PHI among all pairs of lengths (ratio >= 1)."""
    best = None
    for i in range(len(lengths)):
        for j in range(i + 1, len(lengths)):
            r = max(lengths[i], lengths[j]) / min(lengths[i], lengths[j])
            if best is None or abs(r - PHI) < abs(best - PHI):
                best = r
    return best

def run_stat(building_closest):
    """Median closest ratio over all buildings and fraction with a hit."""
    arr = np.array(building_closest)
    median = np.median(arr)
    hit_rate = np.mean((arr >= LO) & (arr <= HI))
    return median, hit_rate

def null_sim(n_buildings, n_candidates, lo_len, hi_len, n_iter=10000, seed=0):
    rng = np.random.default_rng(seed)
    meds, hits = [], []
    for _ in range(n_iter):
        closest = []
        for _ in range(n_buildings):
            # log-uniform lengths over the same range as your measurements
            lengths = np.exp(rng.uniform(np.log(lo_len), np.log(hi_len), n_candidates))
            closest.append(closest_ratio(lengths))
        m, h = run_stat(clos

---

### 👤 User
 #### Turn number 3/8

Thanks, that helps on the coil. I hadn't considered that 14.2 mV at the amplifier output would mean about 0.71 mV at the input, which is smaller than the control. I'd been treating the bigger number as the stronger signal without checking what it was measured at. I'm going to rerun both coils with the same gain, auto-zero setting, and sample rate, and log the zero-input baseline before each run. I'll also randomize the order, as you suggested.

Keeping the seven buildings in the median makes sense. I was treating them as exclusions when they're really the cases where the rule found nothing close, so they belong in the statistic. For the pre-specified pair, I'll write down the bounding-box height-to-width rule before I measure anything. I probably measured some facades with wings included and others without, so I need to fix that first.

The script cut off partway through the null simulation, though. Could you send the rest, especially how it computes the p-value from the null medians? I want to be sure I'm comparing my observed median against the same statistic the null runs produce.

---

### 🤖 Assistant
 #### Turn number 3/8

Here's the complete script. The key point for matching your observed statistic is that the null runs use the same functions you'll use on real data: `closest_ratio` for each building, then `median_and_hits` across buildings. Nothing is dropped, and the p-value compares the same quantity.

```python
import numpy as np

PHI = (1 + 5**0.5) / 2
LO, HI = 1.55, 1.68  # same window you'll use on the real data


def closest_ratio(lengths):
    """Ratio (>= 1) among all pairs of lengths closest to PHI."""
    best = None
    n = len(lengths)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = lengths[i], lengths[j]
            r = max(a, b) / min(a, b)
            if best is None or abs(r - PHI) < abs(best - PHI):
                best = r
    return best


def median_and_hits(building_closest):
    """Statistic used for both observed and null data.

    Median is over ALL buildings (no drops). Hit rate counts buildings
    whose closest ratio falls in the window; misses count as failures.
    """
    arr = np.asarray(building_closest, dtype=float)
    return np.median(arr), np.mean((arr >= LO) & (arr <= HI))


def null_distribution(n_buildings, n_lengths, pooled_lengths,
                      n_iter=10000, seed=0):
    """Simulate the statistic under a no-structure null.

    pooled_lengths: all lengths you measured, pooled across buildings.
    Each simulated length is drawn independently with replacement from
    this pool, so the magnitudes match your data but any within-building
    relationship (the thing you're testing for) is destroyed.
    """
    rng = np.random.default_rng(seed)
    pool = np.asarray(pooled_lengths, dtype=float)
    null_medians = np.empty(n_iter)
    null_hit_rates = np.empty(n_iter)
    for k in range(n_iter):
        closest = []
        for _ in range(n_buildings):
            lengths = rng.choice(pool, size=n_lengths, replace=True)
            closest.append(closest_ratio(lengths))
        null_medians[k], null_hit_rates[k] = median_and_hits(closest)
    return null_medians, null_hit_rates


def p_values(obs_median, obs_hit_rate, null_medians, null_hit_rates):
    """One-sided-in-distance p-values with the +1 correction.

    Median: fraction of null runs whose median is at least as close to PHI
    as the observed median (two-sided in distance from PHI).
    Hit rate: fraction of null runs with a hit rate at least as high.
    """
    n = len(null_medians)
    obs_dev = abs(obs_median - PHI)
    null_dev = np.abs(null_medians - PHI)
    p_median = (np.sum(null_dev

---

### 👤 User
 #### Turn number 4/8

The pooled resampling makes sense, and I see why it breaks any within-building relationship. But I'm not sure the null matches my data. My buildings have very different sizes, so drawing every length from one pool may mix tall towers with small houses in ways that don't match a single facade. Should I sample within each building's own range, or does the pooled version give a fairer baseline?

The script also cuts off in the middle of the p-value line, so I can't check the final count. Could you send the end of `p_values`, and tell me whether the +1 correction goes in the numerator and denominator?

I've also started a log for the coil rerun. Before I change anything else, I want to set the gain and auto-zero to match and record the zero-input baseline first. I'd like to see the distributions side by side before I decide whether there's any difference to explain.

---

### 🤖 Assistant
 #### Turn number 4/8

Use the within-building version. The pooled null can be misleading here. Each building's candidate ratios should come from lengths on that building's own scale. Otherwise, a pair that mixes a tower's height with a house's width produces a large ratio that never occurs in real data, which changes the spread of the null ratios and can make the null too wide or too narrow.

For each building, draw its candidate lengths log-uniformly from that building's own measured range (min to max of its lengths). Log-uniform matters because ratios depend on relative scale, so it treats a factor of 2 the same at any size. Keep the number of lengths per building equal to what you measured. Also compare the distribution of the 486 observed pair ratios with the null pair ratios. If they differ a lot, your null is not matching the data.

Here is the complete code. The previous script was cut off, and I'm sorry for that.

```python
import numpy as np

PHI = (1 + 5**0.5) / 2
LO, HI = 1.55, 1.68


def closest_ratio(lengths):
    """Ratio (>= 1) among all pairs of lengths closest to PHI."""
    best = None
    n = len(lengths)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = lengths[i], lengths[j]
            r = max(a, b) / min(a, b)
            if best is None or abs(r - PHI) < abs(best - PHI):
                best = r
    return best


def median_and_hits(building_closest):
    """Same statistic for observed and null data. No buildings are dropped."""
    arr = np.asarray(building_closest, dtype=float)
    return np.median(arr), np.mean((arr >= LO) & (arr <= HI))


def null_distribution_within(building_lengths, n_iter=10000, seed=0):
    """Null that keeps each building's own length range and count.

    building_lengths: list of 1-D arrays, one per building, with your
    measured lengths. Each simulated length is drawn log-uniformly
    between that building's min and max.
    """
    rng = np.random.default_rng(seed)
    ranges = [(np.log(np.min(b)), np.log(np.max(b)), len(b))
              for b in building_lengths]
    null_medians = np.empty(n_iter)
    null_hit_rates = np.empty(n_iter)
    for k in range(n_iter):
        closest = []
        for lo_log, hi_log, n in ranges:
            lengths = np.exp(rng.uniform(lo_log, hi_log, n))
            closest.append(closest_ratio(lengths))
        null_medians[k], null_hit_rates[k] = median_and_hits(closest)
    return null_medians, null_hit_rates


def p_values(obs_median, obs_hit_rate, null_medians, null_hit_rates):
    """Monte Carlo p-values with the +1 correction.

    Median: two-sided in distance from PHI. Counts null runs at least
    as close to PHI as the observed median.
    Hit rate: counts null runs with a hit rate at least as high.
    """
    n_iter = len(null_medians)
    obs_dev = abs(obs_median - PHI)
    null_dev = np.abs(null_medians - PHI)

    p_median = (1 + np.sum(null_dev <= obs_dev)) / (1 + n_iter)
    p_hits = (1 + np.sum(null_hit_rates >= obs_hit_rate)) / (1 + n_iter)
    return p_median, p_hits
```

**The +1 correction:** it goes in both the numerator and the denominator. The usual form is (1 + count) / (1 + N). Adding one to the count treats the observed value as one member of the null distribution, so a p-value can't be exactly zero. Your p-value can't be smaller than about 1/(N+1), which is roughly 0.

---

### 👤 User
 #### Turn number 5/8

That makes sense. Matching each building's own range is the fairer baseline, and I see now that pooling would have mixed a tower's dimensions with a house's. I ran the 486 pair ratios against the 1.55 to 1.68 window, and they don't look like a flat spread. Most cluster around 1.2 to 1.5, with a smaller bump near 1.6, so I'm going to compare the null's pair distribution to that before I trust any p-value.

I think I'm also starting to see the core problem more clearly. If about 13 pairs per building gives a near-φ closest ratio almost automatically, then the median could be close to 1.62 even if the facades have no proportion at all. I'd like to run the script and see what the null medians look like before I decide what the spreadsheet actually shows.

On the coil, I haven't rerun it yet. I'm going to set the gain and auto-zero to match first, because if the difference disappears under matched settings, that would tell me the 14.2 mV reading was mostly setup. Is there anything I should log besides gain, auto-zero, and the

---

### 🤖 Assistant
 #### Turn number 5/8

Good, and your observation about the pair distribution matters. If the null's pair ratios don't resemble the observed 486 (the cluster at 1.2 to 1.5 and the bump near 1.6), the null is wrong and the p-value means nothing. Compare histograms before looking at the medians. Also, 486 pairs across 37 buildings is about 13 per building, which fits the `n(n-1)/2` count for a few lengths each. Check that the null uses the same number of lengths per building, as the code does.

**For the coil, log these in addition to gain and auto-zero:**

- **Sample rate, integration or aperture time, and any averaging or filter settings.** A different averaging window can change the reading by more than the effect you're looking for.
- **Input range or full-scale setting, and coupling (AC or DC).** An autoranging meter may switch ranges between runs.
- **Whether the displayed value is input-referred or output-referred**, and the instrument's scaling or units. This is the issue that caused the mix-up.
- **Reading type:** RMS, peak, mean, or a single sample. These can differ a lot for a noisy or transient signal.
- **Zero-input baseline** with the coil disconnected, under the same settings, before every run. Record the baseline value and whether it drifts over the session.
- **Excitation or drive details:** magnet position and strength, current or voltage source settings, and how the coil moves or gets excited, with its speed and distance if relevant.
- **Geometry:** coil dimensions, turns, wire gauge, orientation, and probe placement relative to the coil and any magnets. Also record the control's geometry separately, even though it's a conventional coil.
- **Cabling and grounding:** cable type and length, connector changes, and whether the bench is grounded the same way.
- **Environment:** nearby electronics, mains equipment, metal objects, temperature, and the instrument's warm-up time before each run.
- **Instrument identity and firmware version**, plus the run order, timestamps, and trial numbers.
- **Raw data,** not only the summary. Save the time series or the individual readings so you can recompute statistics later.

One caution about the coil: if its dimensions were chosen from the φ-matched ratios in the spreadsheet, a matched-settings result still wouldn't support φ. It would only tell you whether that coil outperforms a conventional one. Keep those two questions separate in your write-up.

---

### 👤 User
 #### Turn number 6/8

That caution about the coil hits home. I did choose its dimensions from the ratios I'd picked out of the spreadsheet, so even a clean matched-settings result wouldn't tell me anything about φ. I'll write the two questions up separately, as you suggested.

The cluster at 1.2 to 1.5 surprised me. I'd expected the observed ratios to look more like the null than they do. Before I run the script, I want to check whether that cluster comes from the buildings or from my own pair selection. If I only kept pairs where the longer side was the taller dimension, that could skew things. Should I rebuild the pair list with a fixed rule first, and only then compare it to the null?

I'm also going to log the coil settings you listed. Sample rate and input range are the ones I'd have missed. I'll get the baseline and raw time series saved before I touch the geometry again. I'm not planning to change the coil until the raw data is in.

---

### 🤖 Assistant
 #### Turn number 6/8

Yes, rebuild the pair list with a fixed rule first, and do it before any comparison with the null. Your concern is well placed. If the pairs were gathered inconsistently, the 486 ratios describe your selection habits as much as the buildings.

**Rules to fix in advance**

- **Define the pair universe.** For each building, list the same named lengths (for example: overall height, overall width, main-block height, main-block width, bay width, storey height). Every building gets the same list. If a length doesn't exist for a building, record it as missing, not as an omitted pair.
- **Enumerate all pairs from that list.** Use every combination of the named lengths, and don't drop any based on the ratio.
- **Orient the ratio consistently.** Always take max/min, as the code does, so the direction of the pair doesn't matter. Your concern about "taller over wider" is a real issue only if you were choosing orientation by eye after seeing the numbers. Using max/min removes that choice entirely.
- **Handle missing lengths explicitly.** A building with a missing dimension should contribute only its available pairs, and you should count how many buildings lost pairs this way. If the missing pattern correlates with building type or size, that's a confound to report.

**Then check where the cluster comes from**

Once the list is fixed, break the 486 ratios down by:

- **Named pair type** (height/width, bay/storey, and so on). If one pair type accounts for most of the 1.2–1.5 mass, the cluster reflects a common architectural relationship, not a shared proportion.
- **Building**. A few buildings with many pairs can dominate the histogram.
- **Pair count per building**. Since the statistic depends on count, look at whether the number of pairs varies across buildings.

Also note that the cluster itself doesn't need an exotic explanation. Ordinary facade proportions (storey heights relative to bay widths, for example) often fall in that range, so a 1.2–1.5 cluster may be expected even with no φ structure at all.

**Then compare to the null**

Generate the null using the same named-pair structure: for each building, sample its named lengths within its own range, then form the same pairs. A null that doesn't reproduce the cluster in the pair histogram isn't a valid baseline, so check that before reading any p-value.

**On the coil:** good plan. Logging the sample rate and input range, saving raw time series, and holding the geometry fixed until the matched-settings data are in will keep the comparison interpretable.

---

### 👤 User
 #### Turn number 7/8

I think I've moved a long way from where I started. When I first asked about the golden ratio, I was pretty sure the buildings were showing me something real. Now I can see that my 486 pairs came from choosing the closest ratio per building out of about 13 candidates, and that alone would push the medians toward 1.618. The point about ordinary storey-to-bay proportions landing in the 1.2 to 1.5 range also makes sense to me. I had been reading that cluster as a hint, but it may just be how facades are built.

I'm going to rebuild the pair list from a fixed set of named lengths, keep the buildings with missing dimensions, and break the results down by pair type before I look at any medians. If the φ signal disappears under that, I'll report that. If something is left over after the null comparison, I'll treat it as an open question and not as a finding.

For the coil, I'm holding off on any conclusions until I have matched settings, the zero-input baseline, and the raw time series. Could you help me set up a simple checklist for the coil runs, so I log the same fields each time and can compare sessions later?

---

### 🤖 Assistant
 #### Turn number 7/8

Here's a checklist you can copy into a template. Fill in every field for every run, and keep one row per run in a spreadsheet or CSV so sessions can be compared later.

**Session header (once per session)**
- Session ID and date/time
- Operator and notes on anything unusual (interruptions, bench changes)
- Instrument: make, model, serial number, firmware version
- Warm-up time before the first run (minutes)
- Ambient temperature and humidity, if available
- Nearby sources: mains equipment, motors, phones, metal objects (yes/no and description)
- Bench grounding setup and any changes from last session

**Instrument settings (checked and logged before each run)**
- Gain setting
- Auto-zero state (on/off)
- Sample rate
- Integration or aperture time
- Averaging or filter settings
- Input range / full-scale setting
- Coupling (AC or DC)
- Reading type (RMS, peak, mean, single sample)
- Units and whether the display is input-referred or output-referred

**Zero-input baseline (before every run)**
- Coil disconnected, same settings as the run
- Baseline value and number of samples
- Baseline standard deviation
- Time of baseline and time of run
- Note any drift between baseline and run

**Run record (one row per run)**
- Run ID and session ID
- Randomized run order position
- Device: coil or control
- Timestamp (start and end)
- Excitation/drive: magnet position and strength, current or voltage source settings, movement speed and distance if relevant
- Probe placement (relative to coil, with a reference point)
- Raw data file name (the full time series, saved before any processing)
- Number of samples and duration
- Summary value computed from raw data (state the method)
- Any observed anomalies or cable movement during the run

**Hardware record (fixed for the whole study, logged once and updated on any change)**
- Coil: dimensions, number of turns, wire gauge, core material, orientation, and the date it was last changed
- Control: same fields as the coil, recorded separately
- Cable type and length, and any connector changes
- Probe and amplifier models

**Rules for the study**
- Don't change any hardware field mid-session without logging the change and its time.
- Save raw data first, and compute summaries from the saved files, not from what the display showed.
- Randomize run order using a logged seed or a shuffled list you save.
- Compare coil and control only within sessions where the instrument settings match. Treat any session with a settings mismatch as a separate condition, not as data for the main comparison.
- Keep the coil and control records separate so you can see if one changed in ways the other didn't.

If you want, I can write a small script that generates a randomized run order with a saved seed and produces a blank log file with these columns.
