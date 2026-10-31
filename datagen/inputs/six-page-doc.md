# Smart Milk Substitution: A Strategic Proposal

*Prepared with AI assistance for the Ordering product team.*

## 1. Executive Summary

In today's fast-moving specialty coffee market, customer expectations for personalization, convenience and reliability have never been higher. Brew Board has an opportunity to turn one of its most frequent customer pain points, milk sell-outs, into a moment of delight. This proposal introduces **Smart Milk Substitution (SMS)**, an intelligent, data-driven capability that detects when a customer's preferred milk is unavailable and proactively recommends the best alternative, personalized to each customer's taste profile, dietary needs and purchase history.

We estimate that Smart Milk Substitution can reduce sell-out-related cart abandonment by up to 40%, increase average order value by 3 to 5%, and improve customer satisfaction scores by 8 to 12 points. The solution builds on our existing real-time inventory signals, our cart infrastructure and our analytics platform, and it can be delivered in three phases over two quarters.

## 2. Background and Problem Statement

Plant-based milks have grown into a significant share of our milk-based beverage sales. Oat milk, in particular, has become the preferred choice for a large and growing segment of our customers. Supply of oat milk is constrained by delivery schedules and storage capacity at each store, and demand peaks are difficult to forecast.

When a milk sells out, the barista marks it as unavailable on the board, and the change is reflected in real time in the customer app. Customers who prefer that milk must then choose another option or leave. Today, the app offers no guidance at this moment. The customer sees a disabled option and must decide on their own.

Our current cart abandonment rate is approximately 7.5%, according to the operations dashboard. Industry research suggests that a significant portion of abandonment in food and beverage ordering is driven by unavailability of preferred items. Customer feedback confirms that sell-outs are a recurring frustration.

### 2.1 Key Pain Points

1. **Lack of guidance.** Customers do not know which alternative will best match their preferred taste and texture.
2. **Lost revenue.** Customers who cannot find an acceptable alternative abandon their orders.
3. **Brand perception.** Repeated sell-outs signal unreliability and erode loyalty.
4. **Operational friction.** Baristas spend time explaining alternatives at the counter.

## 3. Customer Personas

**Olivia, the Oat Loyalist (28).** Orders an oat latte four times a week. Values sustainability and consistency. When oat is unavailable, she is likely to leave and visit a competitor.

**Marcus, the Busy Commuter (41).** Orders ahead every morning. Values speed above all. Will accept any reasonable alternative if it is suggested quickly.

**Priya, the Health-Conscious Explorer (34).** Enjoys trying new drinks. Open to alternatives if she understands the nutritional differences.

**Daniel, the Dairy-Free Parent (38).** Orders for his family. Requires dairy-free options. Needs confidence that any substitute meets dietary restrictions.

## 4. Proposed Solution

Smart Milk Substitution consists of four integrated components.

### 4.1 Real-Time Availability Detection

The system subscribes to inventory events from the barista board. When a milk is marked unavailable, the event is propagated to all active customer sessions within milliseconds, ensuring no customer can order an unavailable item.

### 4.2 Personalized Recommendation Engine

A machine learning model ranks available alternatives for each customer. Features include:

- the customer's order history and milk preferences;
- taste and texture similarity between milks (creaminess, sweetness, foam quality);
- dietary flags (dairy-free, nut-free, lactose-free);
- time of day and drink type;
- popularity of each alternative among similar customers.

The model will be trained on historical order data and continuously refined using acceptance feedback. A rules-based fallback ensures recommendations are always available, even for new customers.

### 4.3 Seamless In-App Experience

When a customer selects a sold-out milk, a friendly bottom sheet appears: *"Oat is out right now. Customers like you love almond in this drink. Swap with one tap?"* The sheet shows the recommended alternative, its price difference, and a brief taste note. Customers can accept, choose another option, or opt to be notified when their milk is back.

### 4.4 Loyalty Integration

To soften the disappointment, customers who accept a substitute receive 25 bonus loyalty points. This encourages trial of alternatives and reinforces brand goodwill.

## 5. Success Metrics

| Metric | Baseline | Target |
|---|---|---|
| Sell-out-related abandonment | 7.5% | 4.5% |
| Substitute acceptance rate | n/a | 60% |
| Average order value | $5.40 | $5.62 |
| CSAT (ordering) | 72 | 82 |
| Barista time per sell-out interaction | 45 s | 10 s |

## 6. Technical Approach

The solution will be implemented as a microservice that integrates with the ordering API, the inventory event stream and the customer profile service. Recommendations will be served from a low-latency cache with a p99 latency target of 50 ms. The order line will record both the requested and the substituted milk, enabling accurate inventory reconciliation and analytics. Events will flow to the data warehouse to power a new Substitution Insights dashboard.

### 6.1 Data Requirements

- Order history (available in the warehouse).
- Inventory events (available in real time).
- Customer dietary preferences (new: collected via an optional profile prompt).
- Substitution acceptance events (new).

### 6.2 Privacy and Compliance

Dietary data will be treated as sensitive personal data. Customers will opt in explicitly. Data will be retained for 24 months and can be deleted on request.

## 7. Rollout Plan

**Phase 1 (Weeks 1 to 4): Foundation.** Real-time detection, rules-based recommendations, the bottom sheet UI, and instrumentation.

**Phase 2 (Weeks 5 to 10): Personalization.** Train and deploy the recommendation model; A/B test against rules-based recommendations.

**Phase 3 (Weeks 11 to 16): Loyalty and Insights.** Loyalty integration, the Substitution Insights dashboard, and expansion to other sold-out items such as syrups and pastries.

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Low acceptance of substitutes | Medium | High | Personalization, loyalty incentive |
| Model bias toward popular milks | Medium | Medium | Diversity constraints in ranking |
| Allergy incidents | Low | High | Strict dietary filters, clear labeling |
| Integration complexity | Medium | Medium | Phased rollout, feature flags |
| Barista adoption | Low | Medium | Training, board indicators |

## 9. Competitive Landscape

Leading quick-service brands have invested heavily in personalization. Customers increasingly expect apps to anticipate their needs. Smart Milk Substitution positions Brew Board as an innovator in the specialty coffee segment and creates a foundation for broader personalization initiatives.

## 10. Investment and Return

We estimate the initiative requires two engineers, one data scientist, one designer and a product manager for two quarters. Based on recovered abandonment and increased order value, we project a payback period of under six months.

## 11. Open Questions

- Should substitution be automatic for customers who opt in?
- Should we extend the solution to syrups and food items in Phase 1?
- How should we communicate the change to baristas?

## 12. Conclusion

Smart Milk Substitution transforms a frustrating moment into an opportunity to demonstrate that Brew Board knows and cares about its customers. By combining real-time inventory, personalized recommendations and loyalty incentives, we can reduce abandonment, grow revenue and strengthen loyalty. We recommend approving Phase 1 to begin next sprint.
