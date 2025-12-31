# 4-Level Hierarchical Topic System

## Overview

The topic categorization system now supports **up to 4 levels of hierarchy**, allowing for sophisticated organization of publications:

```
Level 1: Topic (e.g., "Computer Science")
    └── Level 2: Branch (e.g., "Artificial Intelligence")
        └── Level 3: Sub-branch (e.g., "Machine Learning")
            └── Level 4: Specialization (e.g., "Deep Learning")
```

---

## Hierarchy Structure

### Example 4-Level Structure

```
 Computer Science (Topic)
├──  Artificial Intelligence (Level 1 Branch)
│   ├──  Machine Learning (Level 2 Branch)
│   │   ├──  Deep Learning (Level 3 Branch)
│   │   │   ├── Convolutional Neural Networks (Level 4)
│   │   │   ├── Recurrent Neural Networks (Level 4)
│   │   │   └── Transformers (Level 4)
│   │   ├── Reinforcement Learning (Level 3 Branch)
│   │   └── Supervised Learning (Level 3 Branch)
│   ├──  Natural Language Processing (Level 2 Branch)
│   │   ├── Text Classification (Level 3 Branch)
│   │   ├── Named Entity Recognition (Level 3 Branch)
│   │   └── Machine Translation (Level 3 Branch)
│   └──  Computer Vision (Level 2 Branch)
│       ├── Object Detection (Level 3 Branch)
│       ├── Image Segmentation (Level 3 Branch)
│       └── Face Recognition (Level 3 Branch)
├──  Databases (Level 1 Branch)
│   ├── Relational Databases (Level 2 Branch)
│   ├── NoSQL Databases (Level 2 Branch)
│   └── Graph Databases (Level 2 Branch)
└──  Cybersecurity (Level 1 Branch)
    ├── Network Security (Level 2 Branch)
    ├── Cryptography (Level 2 Branch)
    └── Ethical Hacking (Level 2 Branch)
```

---

## API Changes

### Creating Hierarchical Branches

**Level 1 Branch (under Topic):**

```bash
POST /api/publications/topics/1/branches/
{
  "name": "Artificial Intelligence",
  "slug": "artificial-intelligence",
  "description": "AI research and applications"
}
```

**Response:**

```json
{
  "id": 1,
  "topic_id": 1,
  "parent_id": null,
  "level": 1,
  "full_path": "Computer Science > Artificial Intelligence"
}
```

**Level 2 Branch (under Level 1):**

```bash
POST /api/publications/topics/1/branches/
{
  "name": "Machine Learning",
  "slug": "machine-learning",
  "parent": 1,
  "description": "ML algorithms and techniques"
}
```

**Response:**

```json
{
  "id": 2,
  "topic_id": 1,
  "parent_id": 1,
  "parent_name": "Artificial Intelligence",
  "level": 2,
  "full_path": "Computer Science > Artificial Intelligence > Machine Learning"
}
```

**Level 3 Branch (under Level 2):**

```bash
POST /api/publications/topics/1/branches/
{
  "name": "Deep Learning",
  "slug": "deep-learning",
  "parent": 2,
  "description": "Neural networks with multiple layers"
}
```

**Response:**

```json
{
  "id": 3,
  "topic_id": 1,
  "parent_id": 2,
  "parent_name": "Machine Learning",
  "level": 3,
  "full_path": "Computer Science > AI > Machine Learning > Deep Learning"
}
```

**Level 4 Branch (deepest level):**

```bash
POST /api/publications/topics/1/branches/
{
  "name": "Convolutional Neural Networks",
  "slug": "convolutional-neural-networks",
  "parent": 3,
  "description": "CNNs for image processing"
}
```

**Response:**

```json
{
  "id": 4,
  "topic_id": 1,
  "parent_id": 3,
  "parent_name": "Deep Learning",
  "level": 4,
  "full_path": "Computer Science > AI > ML > Deep Learning > CNNs"
}
```

---

## New API Features

### 1. Filter Branches by Parent

**Get root-level branches (default):**

```bash
GET /api/publications/topics/1/branches/
```

**Get children of specific branch:**

```bash
GET /api/publications/topics/1/branches/?parent=2
```

Returns all branches where `parent_id = 2`

### 2. Hierarchical Topic Detail

**GET `/api/publications/topics/{id}/`** now returns nested tree structure:

```json
{
  "id": 1,
  "name": "Computer Science",
  "branches": [
    {
      "id": 1,
      "name": "Artificial Intelligence",
      "level": 1,
      "full_path": "Computer Science > Artificial Intelligence",
      "children_count": 3,
      "publications_count": 145,
      "children": [
        {
          "id": 2,
          "name": "Machine Learning",
          "level": 2,
          "full_path": "Computer Science > AI > Machine Learning",
          "children_count": 3,
          "publications_count": 78,
          "children": [
            {
              "id": 3,
              "name": "Deep Learning",
              "level": 3,
              "full_path": "CS > AI > ML > Deep Learning",
              "children_count": 3,
              "publications_count": 45,
              "children": [
                {
                  "id": 4,
                  "name": "CNNs",
                  "level": 4,
                  "children": []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 3. Branch Detail with Children

**GET `/api/publications/topics/1/branches/2/`**

```json
{
  "id": 2,
  "topic_id": 1,
  "topic_name": "Computer Science",
  "parent_id": 1,
  "parent_name": "Artificial Intelligence",
  "name": "Machine Learning",
  "slug": "machine-learning",
  "level": 2,
  "full_path": "Computer Science > AI > Machine Learning",
  "children_count": 3,
  "publications_count": 78,
  "children": [
    {
      "id": 3,
      "name": "Deep Learning",
      "level": 3,
      "full_path": "CS > AI > ML > Deep Learning",
      "publications_count": 45
    },
    {
      "id": 5,
      "name": "Reinforcement Learning",
      "level": 3,
      "publications_count": 20
    }
  ]
}
```

---

## Model Changes

### TopicBranch Model (Updated)

| Field       | Type              | Description                           |
| ----------- | ----------------- | ------------------------------------- |
| **parent**  | ForeignKey(self)  | Parent branch (null for level 1)      |
| **level**   | Integer           | Auto-calculated hierarchy level (1-4) |
| topic       | ForeignKey(Topic) | Parent topic                          |
| name        | String            | Branch name                           |
| slug        | SlugField         | URL-friendly identifier               |
| description | Text              | Description                           |
| is_active   | Boolean           | Active status                         |
| order       | Integer           | Display order                         |

### New Properties

- **`full_path`**: Complete hierarchical path (e.g., "CS > AI > ML > Deep Learning")
- **`children_count`**: Number of immediate children
- **`publications_count`**: Count including all descendant branches

### Constraints

- **Unique Together**: (topic, parent, slug)
- **Max Level**: 4 levels deep
- **Auto-Level**: Level is automatically calculated based on parent
- **Cascading**: Deleting a branch deletes all its children

---

## Validation Rules

### Creating Branches

**Valid:**

```json
{
  "parent": 1, // Parent at level 3
  "name": "New Branch"
}
// Creates level 4 branch
```

**Invalid:**

```json
{
  "parent": 25, // Parent already at level 4
  "name": "Another Branch"
}
// Error: "Maximum hierarchy depth is 4 levels"
```

**Invalid:**

```json
{
  "topic": 1,
  "parent": 15, // Parent belongs to topic 2
  "name": "Branch"
}
// Error: "Parent branch must belong to the same topic"
```

---

## Use Cases

### 1. Publications at Any Level

Publications can be tagged with branches at **any level**:

```bash
# Tag with level 1 branch
POST /api/publications/
{
  "title": "General AI Survey",
  "topic_branch": 1  // Artificial Intelligence
}

# Tag with level 4 branch (most specific)
POST /api/publications/
{
  "title": "CNN Architecture Improvements",
  "topic_branch": 4  // Convolutional Neural Networks
}
```

### 2. Browse by Hierarchy Level

```bash
# All AI publications (includes all sub-branches)
GET /api/publications/topics/1/branches/1/publications/

# Only Deep Learning publications (includes level 4 branches)
GET /api/publications/topics/1/branches/3/publications/

# Only CNN publications (most specific)
GET /api/publications/topics/1/branches/4/publications/
```

### 3. Navigate Tree Structure

```bash
# Start at topic
GET /api/publications/topics/1/

# Get level 1 branches
GET /api/publications/topics/1/branches/

# Get children of AI
GET /api/publications/topics/1/branches/?parent=1

# Get children of Machine Learning
GET /api/publications/topics/1/branches/?parent=2
```

---

## Admin Panel Features

### Hierarchical Display

The admin panel now shows indented hierarchy:

```
Topic: Computer Science
  Branches:
    - Artificial Intelligence (Level 1)
    —— Machine Learning (Level 2)
    ———— Deep Learning (Level 3)
    —————— CNNs (Level 4)
    —————— RNNs (Level 4)
    ———— Reinforcement Learning (Level 3)
    —— Natural Language Processing (Level 2)
    ———— Text Classification (Level 3)
```

### Filters Available

- Filter by topic
- Filter by level (1, 2, 3, or 4)
- Filter by parent branch
- Filter by active status

---

## Migration Notes

### Existing Data

If you have existing `TopicBranch` records:

- All will be set to `level = 1` by default
- `parent` field will be `null`
- No data loss occurs

### Updating Existing Branches

```bash
# Update to make a branch a child of another
PATCH /api/publications/topics/1/branches/5/
{
  "parent": 2
}
# Level automatically becomes parent.level + 1
```

---

## Performance Considerations

### Database Indexes

Indexes are created on:

- `(topic, parent, level)` - For efficient tree queries
- `(topic, is_active, order)` - For listing

### Recursive Queries

The `publications_count` property uses recursive queries. For large trees, this may be cached in the future.

---

## Example Workflow

### Admin Creates 4-Level Structure

```bash
# 1. Create Topic
POST /api/publications/topics/
{"name": "Computer Science", "slug": "cs"}

# 2. Create Level 1 Branch
POST /api/publications/topics/1/branches/
{"name": "AI", "slug": "ai"}

# 3. Create Level 2 Branch
POST /api/publications/topics/1/branches/
{"name": "Machine Learning", "slug": "ml", "parent": 1}

# 4. Create Level 3 Branch
POST /api/publications/topics/1/branches/
{"name": "Deep Learning", "slug": "dl", "parent": 2}

# 5. Create Level 4 Branch
POST /api/publications/topics/1/branches/
{"name": "CNNs", "slug": "cnns", "parent": 3}
```

### Author Publishes to Specific Branch

```bash
POST /api/publications/
{
  "title": "Novel CNN Architecture",
  "topic_branch": 4,  // CNNs (level 4)
  "publication_type": "journal_article"
}
```

### User Browses Hierarchy

```bash
# Browse all topics
GET /api/publications/topics/

# View Computer Science with full tree
GET /api/publications/topics/1/

# View all AI publications (includes ML, DL, CNNs)
GET /api/publications/topics/1/branches/1/publications/

# View only CNN publications
GET /api/publications/topics/1/branches/4/publications/
```

---

## Benefits of 4-Level Hierarchy

**Precise Categorization**: Highly specific classification  
 **Flexible**: Can use 1, 2, 3, or 4 levels as needed  
 **Discoverable**: Users can browse from general to specific  
 **Scalable**: Auto-calculated levels prevent errors  
 **Intuitive**: Full path shows complete context  
 **Maintainable**: Easy to reorganize branches

---

## Limitations & Rules

- Maximum depth: **4 levels**
- Cannot create circular references (parent cannot be descendant)
- Topic is inherited from parent (cannot have different topic than parent)
- Deleting a branch deletes all children (cascade delete)
- Publications can only be tagged with one branch (but that branch counts toward all ancestors)

---

## API Endpoints Summary

| Endpoint                                   | Method | Description                                     |
| ------------------------------------------ | ------ | ----------------------------------------------- |
| `/topics/`                                 | GET    | List all topics                                 |
| `/topics/{id}/`                            | GET    | Get topic with full hierarchical tree           |
| `/topics/{id}/branches/`                   | GET    | Get root-level branches (or filter by ?parent=) |
| `/topics/{id}/branches/`                   | POST   | Create new branch (any level, specify parent)   |
| `/topics/{id}/branches/{id}/`              | GET    | Get branch with immediate children              |
| `/topics/{id}/branches/{id}/`              | PATCH  | Update branch (can change parent, move in tree) |
| `/topics/{id}/branches/{id}/`              | DELETE | Delete branch and all descendants               |
| `/topics/{id}/branches/{id}/publications/` | GET    | Browse publications (includes descendants)      |

---
