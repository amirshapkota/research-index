# Follow System Documentation

## Overview
The follow system allows users (both authors and institutions) to follow each other, similar to social media platforms. This creates a network of connections and enables users to stay updated with activity from users they follow.

## Database Model

### Follow Model
Located in `users/models.py`

```python
class Follow(models.Model):
    follower = ForeignKey(CustomUser)      # The user who is following
    following = ForeignKey(CustomUser)     # The user being followed
    created_at = DateTimeField()
    
    # Constraints:
    # - unique_together: ['follower', 'following']
    # - Prevents self-following
```

**Relationships:**
- A user can follow multiple users (one-to-many from follower perspective)
- A user can have multiple followers (one-to-many from following perspective)
- Self-following is prevented through model validation

**Indexes:**
- `['follower', '-created_at']` - Efficiently query who a user follows
- `['following', '-created_at']` - Efficiently query a user's followers

## API Endpoints

All follow endpoints require authentication (`IsAuthenticated` permission).

### 1. Follow a User
**POST** `/api/auth/follow/`

Follow another user (author or institution).

**Request Body:**
```json
{
  "following": 5  // User ID to follow
}
```

**Response (201 Created):**
```json
{
  "message": "Successfully followed user",
  "follow": {
    "id": 1,
    "follower": 3,
    "following": 5,
    "follower_details": {
      "id": 3,
      "email": "john@example.com",
      "user_type": "author",
      "name": "Dr. John Smith",
      "profile_picture": "http://example.com/media/profiles/authors/john.jpg",
      "user_profile_type": {
        "institute": "MIT",
        "designation": "Professor"
      }
    },
    "following_details": {
      "id": 5,
      "email": "jane@example.com",
      "user_type": "author",
      "name": "Prof. Jane Doe",
      "profile_picture": "http://example.com/media/profiles/authors/jane.jpg",
      "user_profile_type": {
        "institute": "Stanford",
        "designation": "Associate Professor"
      }
    },
    "created_at": "2026-01-25T10:30:00Z"
  }
}
```

**Errors:**
- `400 Bad Request`: Already following this user or trying to follow yourself
- `404 Not Found`: User to follow does not exist

---

### 2. Unfollow a User
**DELETE** `/api/auth/unfollow/<user_id>/`

Unfollow a user you are currently following.

**Response (200 OK):**
```json
{
  "message": "Successfully unfollowed user"
}
```

**Errors:**
- `404 Not Found`: Not following this user or user doesn't exist

---

### 3. My Followers
**GET** `/api/auth/followers/`

Get a list of all users following you.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": {
      "id": 3,
      "email": "follower@example.com",
      "user_type": "author",
      "name": "Dr. John Smith",
      "profile_picture": "http://example.com/media/profiles/authors/john.jpg",
      "user_profile_type": {
        "institute": "MIT",
        "designation": "Professor"
      }
    },
    "created_at": "2026-01-25T10:30:00Z"
  },
  ...
]
```

---

### 4. Users I Follow
**GET** `/api/auth/following/`

Get a list of all users you are following.

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "user": {
      "id": 5,
      "email": "following@example.com",
      "user_type": "institution",
      "name": "Harvard University",
      "profile_picture": "http://example.com/media/profiles/institutions/harvard.jpg",
      "user_profile_type": {
        "institution_type": "university",
        "city": "Cambridge",
        "country": "USA"
      }
    },
    "created_at": "2026-01-24T15:20:00Z"
  },
  ...
]
```

---

### 5. User's Followers
**GET** `/api/auth/users/<user_id>/followers/`

Get followers of a specific user.

**Response:** Same format as "My Followers"

---

### 6. User's Following
**GET** `/api/auth/users/<user_id>/following/`

Get users that a specific user is following.

**Response:** Same format as "Users I Follow"

---

### 7. My Follow Statistics
**GET** `/api/auth/follow-stats/`

Get follow statistics for the current user.

**Response (200 OK):**
```json
{
  "followers_count": 125,
  "following_count": 87
}
```

---

### 8. User Follow Statistics
**GET** `/api/auth/users/<user_id>/follow-stats/`

Get follow statistics for a specific user and check if you're following them.

**Response (200 OK):**
```json
{
  "followers_count": 125,
  "following_count": 87,
  "is_following": true
}
```

**Note:** `is_following` field is only included when checking another user's stats.

---

## Serializers

### UserBasicSerializer
Provides basic user information for follow lists:
- `id`: User ID
- `email`: User email
- `user_type`: "author", "institution", or "admin"
- `name`: Full name (author) or institution name
- `profile_picture`: URL to profile picture or logo
- `user_profile_type`: Type-specific profile info

### FollowSerializer
Detailed follow relationship with full user information.

### FollowCreateSerializer
For creating new follow relationships with validation.

### FollowerListSerializer
List of followers with basic user details.

### FollowingListSerializer
List of users being followed with basic user details.

### FollowStatsSerializer
Follow statistics (counts and is_following flag).

---

## Usage Examples

### Frontend Integration

#### Follow a User
```typescript
const followUser = async (userId: number) => {
  const response = await fetch('/api/auth/follow/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ following: userId }),
    credentials: 'include', // Include cookies
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log(data.message); // "Successfully followed user"
  }
};
```

#### Get Followers
```typescript
const getMyFollowers = async () => {
  const response = await fetch('/api/auth/followers/', {
    credentials: 'include',
  });
  
  const followers = await response.json();
  return followers;
};
```

#### Check Follow Status
```typescript
const checkFollowStatus = async (userId: number) => {
  const response = await fetch(`/api/auth/users/${userId}/follow-stats/`, {
    credentials: 'include',
  });
  
  const stats = await response.json();
  return stats.is_following; // true or false
};
```

---

## Business Logic

### Follow Rules
1. **No Self-Following**: Users cannot follow themselves
2. **Unique Relationships**: Each follower-following pair is unique (database constraint)
3. **Cross-Type Following**: Authors can follow institutions and vice versa
4. **Automatic Validation**: Duplicate follow attempts return appropriate error messages

### Query Optimization
All list views use `select_related()` to minimize database queries:
```python
Follow.objects.filter(following=user).select_related(
    'follower',
    'follower__author_profile',
    'follower__institution_profile'
)
```

This ensures efficient retrieval of user profiles in a single query.

---

## Admin Interface

The Follow model is registered in Django admin with custom display:
- Shows follower email, type, following email, and type
- Filterable by user type and creation date
- Searchable by email addresses
- Read-only created_at field

**Admin Features:**
```python
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower_email', 'follower_type', 'following_email', 'following_type', 'created_at']
    search_fields = ['follower__email', 'following__email']
    list_filter = ['follower__user_type', 'following__user_type', 'created_at']
```

---

## Database Migration

Migration file: `users/migrations/0006_follow.py`

Creates:
- Follow table with follower and following foreign keys
- Unique constraint on (follower, following)
- Indexes for efficient querying

---

## Future Enhancements

Potential additions to the follow system:

1. **Follow Notifications**
   - Notify users when someone follows them
   - Notify about activity from followed users

2. **Mutual Follows**
   - Detect mutual following relationships
   - Special badges or indicators for mutual connections

3. **Follow Suggestions**
   - Recommend users based on research interests
   - Suggest based on co-author relationships
   - Institution-based suggestions

4. **Follow Feed**
   - Activity feed of publications from followed users
   - Chronological or algorithmic sorting

5. **Follower Privacy**
   - Option to make follower lists private
   - Approve/reject follower requests

6. **Analytics**
   - Track follower growth over time
   - Engagement metrics from followers

---

## Testing

### Manual Testing Checklist

- [ ] Follow a user successfully
- [ ] Cannot follow yourself
- [ ] Cannot follow the same user twice
- [ ] Unfollow works correctly
- [ ] Followers list updates in real-time
- [ ] Following list updates correctly
- [ ] Follow stats are accurate
- [ ] is_following flag works correctly
- [ ] Cross-type following (author ↔ institution)
- [ ] Admin interface displays correctly

### API Testing Examples

```bash
# Follow a user
curl -X POST http://localhost:8000/api/auth/follow/ \
  -H "Content-Type: application/json" \
  -d '{"following": 5}' \
  --cookie "access_token=<token>"

# Get my followers
curl http://localhost:8000/api/auth/followers/ \
  --cookie "access_token=<token>"

# Unfollow a user
curl -X DELETE http://localhost:8000/api/auth/unfollow/5/ \
  --cookie "access_token=<token>"
```

---

## Summary

The follow system provides a robust foundation for social networking features in the research index platform. It allows users to:

- ✅ Follow other users (authors and institutions)
- ✅ View followers and following lists
- ✅ Track follow statistics
- ✅ Check follow status between users
- ✅ Efficiently query relationships

The system is built with performance, validation, and extensibility in mind, ready for future enhancements like notifications and activity feeds.
