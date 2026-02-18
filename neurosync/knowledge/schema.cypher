// NeuroSync AI — Neo4j Knowledge Graph Schema
// Run this file via: cypher-shell -f schema.cypher
// Or execute each statement individually in Neo4j Browser.

// =============================================================================
// Constraints (uniqueness + existence)
// =============================================================================

CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;

CREATE CONSTRAINT student_id_unique IF NOT EXISTS
FOR (s:Student) REQUIRE s.student_id IS UNIQUE;

CREATE CONSTRAINT misconception_id_unique IF NOT EXISTS
FOR (m:Misconception) REQUIRE m.misconception_id IS UNIQUE;

// =============================================================================
// Indexes for fast lookups
// =============================================================================

CREATE INDEX concept_name_idx IF NOT EXISTS
FOR (c:Concept) ON (c.name);

CREATE INDEX concept_category_idx IF NOT EXISTS
FOR (c:Concept) ON (c.category);

CREATE INDEX student_name_idx IF NOT EXISTS
FOR (s:Student) ON (s.name);

// =============================================================================
// Node labels and their expected properties
// =============================================================================
//
// (:Concept {
//     concept_id: String,          -- unique ID (e.g., "photosynthesis")
//     name: String,                -- human-readable name
//     category: String,            -- core | prerequisite | extension | application
//     difficulty: Float,           -- 0.0 to 1.0
//     description: String,         -- brief description
//     subject: String,             -- e.g., "biology", "math"
//     created_at: Float            -- epoch timestamp
// })
//
// (:Student {
//     student_id: String,          -- unique student ID
//     name: String,                -- display name
//     created_at: Float            -- epoch timestamp
// })
//
// (:Misconception {
//     misconception_id: String,    -- unique ID
//     concept_id: String,          -- related concept
//     description: String,         -- what the misconception is
//     common_wrong_answer: String, -- typical wrong answer pattern
//     correction: String,          -- how to fix it
//     severity: Float              -- 0.0 to 1.0
// })

// =============================================================================
// Relationship types
// =============================================================================
//
// (Concept)-[:REQUIRES]->(Concept)
//     Properties: weight (Float), description (String)
//
// (Student)-[:STUDIED]->(Concept)
//     Properties: mastery_score (Float), level (String),
//                 attempts (Int), correct (Int), incorrect (Int),
//                 first_seen (Float), last_seen (Float),
//                 streak (Int), best_score (Float)
//
// (Student)-[:MASTERED]->(Concept)
//     Properties: mastered_at (Float), score (Float)
//
// (Student)-[:STRUGGLES_WITH]->(Concept)
//     Properties: failure_count (Int), last_failure (Float)
//
// (Concept)-[:HAS_MISCONCEPTION]->(Misconception)
//     Properties: frequency (Float)
//
// (Concept)-[:NEXT_CONCEPT]->(Concept)
//     Properties: suggested_order (Int)
