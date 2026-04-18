# NutriVision — Non-Technical Project Report
**AI-Powered Indian Food Nutrition Estimator**
*Group 2 | Data Science & AI Lab, IIT Madras*

---

## What is NutriVision?

NutriVision is an AI-powered web application that analyses a photograph of a meal and automatically identifies the food items in it, estimates how much food is on the plate, and tells you the nutritional content — all without any manual input from the user.

The system was built with Indian cuisine in mind, addressing a real gap in existing nutrition tools which either require users to type in everything manually, assume fixed unrealistic portion sizes, or simply do not recognise Indian dishes at all. NutriVision handles complex multi-dish Indian plates, like a thali, in a single photograph.

---

## The Problem Being Solved

Most nutrition tracking apps today have significant shortcomings:

- They require the user to manually search and log every food item eaten.
- They assume every serving is exactly 100 grams, regardless of how much is actually on the plate.
- They have very poor coverage of Indian regional cuisine.
- None of them estimate the real weight of food from a photo.

NutriVision was built to address all of these problems in one unified, automated system.

---

## How the Final System Works (Non-Technical)

The user simply photographs their meal — with a ₹10 Indian coin placed in the frame as a size reference — and uploads it to the application. The system then works through five automatic steps:

**Step 1 — Identify and outline all food items in the photo**
An AI model scans the image and draws precise outlines around every visible food item, separating food from bowls, plates, and background.

**Step 2 — Use the coin to measure real-world size**
The ₹10 coin (which has a fixed, known diameter of 2.7 cm) acts as a ruler. The system detects the coin in the photo and uses it to calculate the actual physical size of each food item in the image.

**Step 3 — Identify what each food item is**
A food recognition model examines each outlined food item and identifies which of the 80 supported Indian dishes it is — with a very high accuracy rate of nearly 98%.

**Step 4 — Estimate the weight of each item**
Using the real-world dimensions calculated in Step 2, the system geometrically estimates the volume of each food item (for example, treating a bowl of curry like a cylinder) and then multiplies that by the known density of that specific food to arrive at an estimated weight in grams.

**Step 5 — Calculate and display nutrition information**
Using the identified food and its estimated weight, the system looks up the nutritional values from a database of 80 Indian dishes and presents a complete breakdown of calories, carbohydrates, protein, fat, sugar, fibre, sodium, calcium, iron, vitamin C, and folate.

---

## The Application

The final product is a live web application accessible via a browser on any device. It has a clean two-tab interface:

- **Analyse tab** — where users upload or take a photo and receive their nutritional breakdown.
- **Supported Foods tab** — a gallery showing all 79 dishes the system can recognise, grouped by category (Breads & Rice, Snacks & Chaat, Curries & Mains, Sweets & Desserts, and more).

The results appear progressively as each step completes, so the user can see the pipeline working in real time. The final output includes an annotated image with coloured overlays on each detected food item, labelled with the food name and estimated weight, alongside a detailed nutrition table.

---

## How the Project Evolved (Milestones 4–6)

The project underwent a significant evolution over its later milestones. The early approach used a different type of AI model (YOLO-based object detection) and a simple regression model to estimate weight. While functional, this early approach had notable limitations in accuracy and practicality.

From Milestone 4 onwards, the team redesigned the pipeline from the ground up:

- The food detection component was replaced with a more powerful segmentation model (SAM3) that produces precise pixel-level outlines rather than rough bounding boxes, handling overlapping dishes far more naturally.
- Two dedicated food classification models — ConvNeXtV2-Tiny and EfficientNetV2-S — were trained specifically on Indian food images, achieving dramatically higher accuracy than the previous approach.
- The weight estimation method was redesigned from a simple regression model (which required large amounts of labelled data and was sensitive to camera angle) to a geometry-based approach using coin calibration, which is practical, interpretable, and works without any specialist equipment.
- The application was built as a fully streaming web interface with live progress feedback, session management, and a polished user experience.

---

## Results and Performance

### Food Recognition Accuracy

| Model | Accuracy (Top-1) | F1 Score |
|---|---|---|
| EfficientNetV2-S | 92.85% | 0.90 |
| ConvNeXtV2-Tiny | 97.92% | 0.97 |
| Both models combined | 98.00% | 0.98 |

The top-performing model (ConvNeXtV2-Tiny) correctly identified the food in nearly 98 out of every 100 test images. When considering the top 5 predictions, accuracy reaches 99.76%, meaning the correct dish is almost always within the system's top five guesses.

### Real-World Test Results

When tested on actual food photos with a ₹10 coin placed in frame:

| Photo | What the System Detected | Estimated Weight | Estimated Calories |
|---|---|---|---|
| Moong dal halwa in bowl | Moong dal halwa ✅ | 100 g | 350 kcal |
| Steamed momos (stock photo) | Steamed momo ✅ | 37 g | 52 kcal |
| Biryani in steel bowl | Chivda ⚠️ (misclassified) | 25 g | 28 kcal |
| Samosa on foil | Garlic bread ⚠️ (misclassified) | 6 g | 23 kcal |

The two misclassifications have understandable explanations: biryani in a steel bowl photographed from a distance looks visually similar to chivda, and the samosa image was of poor quality. These reflect the inherent challenge of fine-grained Indian food recognition from real-world photographs.

### Where the System Is Most and Least Reliable

The system performs best on foods with distinctive visual appearances — steamed momos, sabudana vada, grilled sandwiches, and most curries are identified with very high accuracy.

The most common errors occur with visually similar pizza variants (chicken vs. paneer vs. margherita pizza, which look nearly identical in photographs) and a small number of food categories that had very few training images. These are acknowledged limitations with clear paths to improvement.

---

## Key Achievements

- A food classifier trained on over 131,000 Indian food images reaching 97.92% accuracy across 80 classes — significantly outperforming general-purpose food recognition tools.
- A practical, hardware-free method of estimating food weight from a single photograph using geometric reasoning and a coin as a reference object.
- A fully deployed, real-time web application handling the entire pipeline end-to-end, from raw photograph to nutritional breakdown.
- A curated nutritional database of 80 Indian dishes with 11 macro- and micronutrients per food item, plus food density values sourced from scientific literature.

---

## Limitations

- A ₹10 coin must be placed in the frame for the weight estimation to work. Without it, the pipeline cannot determine real-world scale.
- The system supports 80 food categories. Any dish outside this set will not be recognised.
- Weight estimates are approximations based on geometry and assumed density values — they will not be as precise as a kitchen scale.
- Very similar-looking foods (particularly pizza variants) are the primary source of classification errors.
- Image quality significantly affects accuracy — low-light, overhead, or blurry photos reduce performance.

---

## What Comes Next

The team has identified several high-impact improvements for future development:

- Completing a full retraining run with optimised settings, expected to push accuracy above 99%.
- Expanding the food database to cover 150+ Indian dishes, including more regional specialties.
- Building a mobile app with on-device processing to reduce response time from around 8 seconds to under 2 seconds.
- Adding daily meal tracking to compare a full day's intake against Indian Council of Medical Research (ICMR) dietary guidelines.
- Allowing users to input their age, gender, and activity level for personalised nutritional recommendations.
- Exploring alternative reference objects (credit cards, standard plate diameters) so a coin is not always required.

---

## Summary

NutriVision represents a substantial step forward in making nutrition tracking accessible and accurate for Indian cuisine. By combining state-of-the-art image segmentation, fine-tuned food classification, and practical geometric weight estimation, the system eliminates the manual effort that makes existing nutrition apps inconvenient to use. With a near-98% food recognition accuracy and a fully deployed web application, the project delivers a working, real-world product while identifying a clear roadmap for continued improvement.

---

*Report prepared based on the NutriVision Final Technical Report — Milestone 6, Group 2, IIT Madras.*
