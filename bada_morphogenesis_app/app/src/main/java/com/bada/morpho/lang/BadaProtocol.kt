package com.bada.morpho.lang

/**
 * A differentiation + manufacturing protocol, declared in a .bada file.
 * Represents simulation parameters only — not a laboratory procedure.
 */
data class BadaProtocol(
    val id: String,
    val label: String,
    val target: String,        // target terminal cell type (Japanese label)
    val fieldStrength: Double,  // abstract morphogenetic-field strength 0..1
    val cuspA: Double,          // cusp control a (negative => bistable)
    val cuspB: Double,          // cusp control b
    val branchProb: Double,     // branch probability 0..1
    val feed: Double,           // Gray-Scott feed
    val kill: Double,           // Gray-Scott kill
    val drug: String,           // simulated drug-candidate name
    val note: String
)
