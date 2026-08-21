# What X's ranking code actually says

Read from `github.com/twitter/the-algorithm`, cloned at commit `c54bec0d4e02`,
"update for-you recommendations code", 3 September 2025. This is the current
public revision, not the 2023 one, and it differs from the 2023 version in ways
that matter.

**The first thing to say: the production weights are not in the repository.**
Every entry in `HomeGlobalParams.ModelWeights` has `default = 0.0` and is set at
runtime by a feature switch. The widely quoted numbers from 2023 ("a reply is
worth 13.5 favourites") are not in this code and cannot be recovered from it.
What the code does tell you, precisely, is **which outcomes are optimised**,
**which multiplicative penalties apply**, and **what gets dropped outright** -
and those are enough to shape a post.

## 1. The thirty scored labels

`home-mixer/server/src/main/scala/com/twitter/home_mixer/param/HomeGlobalParams.scala`

```
bookmark  dwell  dwell_0  dwell_1  dwell_2  dwell_3  dwell_4  fav
good_click  good_click_v1  good_click_v2  good_profile_click
negative_feedback_v2  open_link  profile_dwelled  reply
reply_engaged_by_author  report  retweet  screenshot  share
share_menu_click  strong_negative_feedback  tweet_detail_dwell
video_playback50  video_quality_viewed  video_quality_viewed_immersive
video_quality_watched  video_watch_time_ms  weak_negative_feedback
```

Three readings that change how you write:

- **Seven of the thirty are dwell.** `dwell`, `dwell_0` through `dwell_4`,
  `tweet_detail_dwell`, plus `profile_dwelled`. Time spent is the most
  represented outcome in the entire objective. A post that has to be read beats
  a post that is instantly parsed and scrolled.
- **`reply_engaged_by_author` is its own label**, separate from `reply`. A reply
  that the author answers is a distinct optimisation target. Answering replies
  is not etiquette here, it is the ranked outcome.
- **`bookmark`, `share`, `share_menu_click` and `screenshot`.** Screenshotting a
  post is a scored label. Reference-shaped content - a table, a short list of
  numbers, a rule - is directly optimised for.

`open_link`, `good_click`, `good_click_v1` and `good_click_v2` are **positive**
labels. There is no link penalty anywhere in this code. The common advice to
keep links out of the first post is not supported by the ranker; the argument
for it is that dwell and screenshot accrue whether or not anyone clicks, while
an unopened link contributes nothing.

## 2. The multiplicative penalties, with their defaults

`product/scored_tweets/scorer/HeuristicScorer.scala` multiplies the model score
by the product of about sixteen rescoring factors. The ones with published
defaults:

| Factor | Where | Default |
|---|---|---|
| Out of network | `RescoreOutOfNetwork` | **0.75** |
| Is a reply | `RescoreReplies` | **0.75** |
| Same author, nth post | `AuthorBasedListwiseRescoringProvider` | `(1 - 0.25) * 0.5^n + 0.25` |
| Grok slop score == 3 | `GrokSlopScoreRescorer` | a decay factor below 1 |

**The author-diversity decay is the most important structural fact for a
thread.** With `AuthorDiversityDecayFactor = 0.5` and `AuthorDiversityFloor =
0.25`, posts from one author in a single candidate set are scored:

- 1st post: 1.00
- 2nd post: 0.625
- 3rd post: 0.3125
- 4th and beyond: asymptotically 0.25

A thread does not get many slots in one person's For You. **Post 1 competes;
posts 2 onward mostly do not.** And a self-reply is both a reply (0.75) and, for
non-followers, out of network (0.75), so a thread continuation carries roughly
0.56 before author decay is applied at all.

Conclusion, applied to the launch: post 1 has to be a complete artifact on its
own. The thread is for the people who already stopped.

## 3. A language model grades your post before a human sees it

`functional_component/feature_hydrator/GrokAnnotationsFeatureHydrator.scala`
hydrates every candidate with Grok-generated annotations:

```
GrokIsGoreFeature  GrokIsNsfwFeature  GrokIsSpamFeature  GrokIsViolentFeature
GrokIsLowQualityFeature  GrokIsOcrFeature  GrokSunnyScoreFeature
GrokPoliticalInclinationFeature  GrokSlopScoreFeature  GrokTopCategoryFeature
GrokTagsFeature
```

- `GrokSlopScoreRescorer` multiplies the score of anything scoring 3 on slop by
  a decay factor. Hook bait, thread emoji, "this changes everything" - that is
  precisely the register a slop classifier is trained to catch.
- `SlopFilter` **removes** out-of-network posts from authors flagged as slop
  authors with more than 100 followers (`SlopMinFollowers`, default 100). This
  is author-level reputation, not per-post.
- `GrokIsOcrFeature` detects text rendered inside an image. Screenshots of text
  are visible to the ranker as screenshots of text.
- `GrokTopCategoryFeature`, paired with `UserEngagedGrokCategoriesFeatureHydrator`,
  routes out-of-network distribution through categories the reader already
  engages with. Naming your domain plainly helps the classifier file you
  correctly.

There are also hard filters: `GrokSpamFilter`, `GrokNsfwFilter`,
`GrokGoreFilter`, `GrokViolentFilter`.

## 4. Follower count is normalised out, not multiplied in

`RescoreMTLNormalization` passes `AuthorFollowersFeature` into an
`MtlNormalizer` (`MtlNormalization.EnableMtlNormalizationParam` defaults to
`true`). Predicted engagement is calibrated against the author's follower count,
so a small account is not competing on raw volume. Being small is not the
handicap the folklore says it is.

## 5. Media is deduplicated by visual cluster

`MediaDeduplicationFilter`, `ClipClusterDeduplicationFilter`,
`ClusterBasedDedupFilter`, `ImpressedImageClusterBasedListwiseRescoringProvider`
and `ImpressedMediaClusterBasedListwiseRescoringProvider` all exist. Seven
near-identical teal bar charts are plausibly one media cluster. Vary the chart
shapes across a thread.

## 6. Video is a separate, well-fed lane

Five of the thirty labels are video labels, and there is a supporting cast of
`VIDEO_DURATION`, `BIT_RATE`, aspect-ratio and colour-palette features in
`ContentFeatureAdapter`, plus `MinVideoDurationFilter`,
`MaxVideoDurationFilter` and `ConsistentAspectRatioFilter`. A short video is
worth its own post rather than a slot inside a text thread.

## 7. Negative feedback is graded and cheap for the reader

`weak_negative_feedback`, `strong_negative_feedback`, `negative_feedback_v2` and
`report` are four separate labels, and `RescoreFeedbackFatigue` discounts
authors a reader has previously asked to see less of. One "not interested" costs
the reader a tap and costs you future distribution to that person. Overclaiming
is the cheapest way to buy it, which is a real argument for the self-critical
posts rather than against them.

## What this changed in the thread

| Finding | Change |
|---|---|
| Author decay 1.0, 0.625, 0.3125, 0.25 | Eleven posts cut to seven; post 1 rewritten to stand alone with the full table |
| Seven dwell labels | Post 1 is a table you have to read, not a one-line hook |
| `screenshot`, `bookmark`, `share` are labels | Posts 4 and 5 are plain quotable lists |
| `reply_engaged_by_author` | A real question in the first reply, and a commitment to answer everything |
| `GrokSlopScoreRescorer` | No thread emoji, no "read to the end", no announcement language |
| Media cluster dedup | Three different chart shapes across the thread, not seven bar charts |
| Negative feedback labels | The four self-criticisms stay; they are the opposite of the thing that earns a "not interested" |
| Video labels | The 30 second cut is a separate post on another day, not post 8 |
