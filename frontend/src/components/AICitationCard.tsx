import React from "react"
import { Link } from "react-router-dom"
import type { AICitation } from "../../types"

interface AICitationCardProps {
  citation: AICitation
}

export const AICitationCard: React.FC<AICitationCardProps> = ({ citation }) => {
  const formattedPrice = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(citation.price)

  return (
    <Link
      to={citation.url}
      className="ai-citation-card"
      aria-label={`View product: ${citation.product_name}`}
      title={`View product: ${citation.product_name}`}
    >
      <div className="ai-citation-top">
        <span className="ai-citation-category">{citation.category}</span>
        <span className="ai-citation-price">{formattedPrice}</span>
      </div>
      <h4 className="ai-citation-name">{citation.product_name}</h4>
      <div className="ai-citation-footer">
        <span className={`ai-citation-stock ${citation.stock > 0 ? "in-stock" : "out-of-stock"}`}>
          {citation.stock > 0 ? `In Stock (${citation.stock})` : "Out of Stock"}
        </span>
        <span className="ai-citation-view">View details &rarr;</span>
      </div>
    </Link>
  )
}
