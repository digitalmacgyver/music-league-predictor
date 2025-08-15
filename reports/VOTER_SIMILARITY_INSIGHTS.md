# Music League Voter Similarity Analysis

*Fun insights from analyzing 11,464 votes across 1,738 songs by 25 voters*

## Understanding Similarity Scores

**Similarity scores** range from 0.0 to 1.0 and measure how similarly two voters rate songs:
- **1.0 = Perfect agreement**: Always give the same scores to the same songs
- **0.8-0.9 = Very similar taste**: Usually agree on what's good/bad
- **0.5-0.7 = Moderately similar**: Some overlap in preferences
- **0.3-0.4 = Different taste**: Rarely agree on song ratings
- **0.0 = Opposite taste**: One person's favorites are the other's least favorites

*Note: We use cosine similarity, which focuses on rating patterns rather than absolute score differences*

---

## Voter Similarity Network

### 👥 **Most & Least Compatible Voters**

| Voter | Most Similar To | Score | Least Similar To | Score |
|-------|-----------------|-------|------------------|-------|
| **Adam Gimpert** | Matt M | 0.263 | Adrien | 0.000 |
| **Adrien** | Ben Hamilton | 0.328 | Adam Gimpert | 0.000 |
| **Aezed Raza** | Molly Brennan | 0.462 | Adam Gimpert | 0.000 |
| **Arun Bhalla** | Aezed Raza | 0.288 | Adam Gimpert | 0.000 |
| **Austin Walterman** | Molly Brennan | 0.412 | Adam Gimpert | 0.000 |
| **Ben Chelf** | M. Rose Barlow | 0.126 | Adam Gimpert | 0.000 |
| **Ben Hamilton** | Kirk Hayward | 0.504 | Aezed Raza | 0.000 |
| **caliban** | Joe Hayward | 0.492 | [Left the league] | 0.027 |
| **David Wood** | Arun Bhalla | 0.207 | Adam Gimpert | 0.000 |
| **Drew** | Joe Hayward | 0.581 | Ben Chelf | 0.000 |
| **Jared** | caliban | 0.437 | [Left the league] | 0.016 |
| **Joe Hayward** | Drew | 0.581 | Ben Chelf | 0.000 |
| **Kirk Hayward** | Joe Hayward | 0.531 | Aezed Raza | 0.000 |
| **legion1996a** | Joe Hayward | 0.553 | [Left the league] | 0.030 |
| **M. Rose Barlow** | Austin Walterman | 0.337 | Adam Gimpert | 0.000 |
| **Matt M** | Joe Hayward | 0.562 | Ben Chelf | 0.000 |
| **Molly Brennan** | Aezed Raza | 0.462 | Adam Gimpert | 0.000 |
| **Qui-Jon Jinn** | Joe Hayward | 0.498 | Ben Chelf | 0.000 |
| **Rachel Peterson** | someben | 0.454 | Aezed Raza | 0.000 |
| **someben** | Ben Hamilton | 0.455 | Molly Brennan | 0.000 |
| **William Strickland Hamilton** | Ben Hamilton | 0.360 | Aezed Raza | 0.000 |

---

## 🎵 **Musical Soulmates & Opposites**

### **Perfect Harmony** 🎶
**Drew & Joe Hayward** (0.581 similarity)
- *The ultimate musical soulmates! These two have the highest similarity score, meaning they almost always agree on what makes a great song.*

**Matt M & Joe Hayward** (0.562 similarity)  
- *Another strong musical connection - when Joe loves a song, Matt usually does too*

**legion1996a & Joe Hayward** (0.553 similarity)
- *Joe Hayward seems to be the musical center of gravity for many voters!*

### **The Joe Hayward Effect** 🌟
Joe Hayward appears as the "most similar" voter for **6 different people**:
- Drew, Matt M, legion1996a, Kirk Hayward, caliban, and Qui-Jon Jinn
- *Joe has cultivated taste that resonates with many league members*

### **Musical Oil & Water** 🔥❄️
**Adam Gimpert: The Outlier** 😅
- Adam Gimpert appears as the "least similar" voter for **11 different people**
- Zero similarity (0.000) with many voters including Adrien, Aezed Raza, Arun Bhalla, Austin Walterman, and others
- *Adam marches to the beat of their own drum - very unique musical taste!*

### **The Zero Club** 🎭
Many voters have **0.000 similarity** with Adam Gimpert, suggesting:
- *Completely non-overlapping musical preferences*
- *Different voting strategies or musical backgrounds*
- *Adam's picks are often everyone else's passes*

---

## 🔍 **Interesting Patterns**

### **The Hayward Connection**
- **Joe Hayward** and **Kirk Hayward** have 0.531 similarity
- *Family musical DNA confirmed! These two share genetic AND musical compatibility*

### **The High-Activity Cluster**
The most active voters tend to cluster around Joe Hayward:
- Joe ↔ Drew: 0.581
- Joe ↔ Matt M: 0.562  
- Joe ↔ Kirk: 0.531
- Joe ↔ legion1996a: 0.553
- *Heavy voters develop more refined, consistent taste patterns*

### **The Hamilton Brothers**
- **Ben Hamilton** and **William Strickland Hamilton** show interesting patterns
- Ben Hamilton appears as "most similar" for both Adrien (0.328) and William (0.360)
- *Another family connection in the data!*

### **Partnership Patterns**
Several strong musical partnerships emerge:
- **Aezed Raza & Molly Brennan**: 0.462 similarity (mutual appreciation)
- **Ben Hamilton & someben**: 0.455 similarity  
- **caliban & Jared**: 0.437 similarity

---

## 🏆 **Fun Statistics**

- **Highest similarity pair**: Drew & Joe Hayward (0.581)
- **Lowest similarity pair**: Adam Gimpert & multiple voters (0.000)
- **Most universally liked voter**: Joe Hayward (most similar to 6 different voters)
- **Most contrarian voter**: Adam Gimpert (least similar to 11 different voters)
- **Average similarity score**: 0.169
- **Most similar family members**: Joe & Kirk Hayward (0.531)
- **Most collaborative voters**: The Joe Hayward cluster (Drew, Matt M, legion1996a, Kirk)
- **Biggest musical mystery**: How Adam Gimpert achieved 0.000 similarity with so many people

---

## 🎧 **What This Means for Recommendations**

When Scout uses `--voter` mode, it leverages these similarities:

- **High similarity voters** get weighted recommendations from their "musical soulmates"
- **Joe Hayward's ratings** become powerful signals for Drew, Matt M, legion1996a, and others
- **Adam Gimpert** gets highly personalized recommendations since no one shares their taste
- **Family members** like the Haywards get cross-pollinated recommendations
- **The system learns** that when Drew loves a song, Joe Hayward probably will too

*The beauty of collaborative filtering: your musical taste helps everyone discover great songs!* 🎵

---

*Generated from Music League voting data • Cosine similarity analysis • 25 voters, 1,738 songs, 11,464 votes*