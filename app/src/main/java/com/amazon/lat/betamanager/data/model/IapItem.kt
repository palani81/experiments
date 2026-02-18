package com.amazon.lat.betamanager.data.model

data class IapItem(
    val sku: String,
    val title: String,
    val price: String,
    val type: IapType,
    val purchaseDate: Long?
)

enum class IapType {
    CONSUMABLE,
    ENTITLEMENT,
    SUBSCRIPTION
}
