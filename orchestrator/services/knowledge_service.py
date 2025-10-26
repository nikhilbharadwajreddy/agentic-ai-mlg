"""
Knowledge Service

Handles Firestore operations for company information knowledge base.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from google.cloud import firestore

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service layer for knowledge base management.
    
    Collection: company_info
    - Services, pricing, team, FAQs, policies
    """
    
    def __init__(self, db_client: firestore.Client):
        """
        Initialize knowledge service.
        
        Args:
            db_client: Firestore client
        """
        self.db = db_client
        self.collection = self.db.collection("company_info")
    
    def search_knowledge(
        self, 
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base.
        
        Currently does simple keyword matching.
        Future: Can be enhanced with vector embeddings for semantic search.
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        try:
            # Start with published documents only
            query_ref = self.collection.where("published", "==", True)
            
            # Filter by category if provided
            if category:
                query_ref = query_ref.where("category", "==", category)
            
            # Get all documents
            docs = []
            for doc in query_ref.stream():
                doc_data = doc.to_dict()
                doc_data["doc_id"] = doc.id
                
                # Simple keyword matching
                score = self._calculate_relevance_score(query, doc_data)
                if score > 0:
                    doc_data["relevance_score"] = score
                    docs.append(doc_data)
            
            # Sort by relevance and limit
            docs.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return docs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of documents
        """
        try:
            query = self.collection.where("category", "==", category)\
                                   .where("published", "==", True)\
                                   .order_by("order")
            
            docs = []
            for doc in query.stream():
                doc_data = doc.to_dict()
                doc_data["doc_id"] = doc.id
                docs.append(doc_data)
            
            return docs
            
        except Exception as e:
            logger.error(f"Error getting category {category}: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None
        """
        try:
            doc = self.collection.document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["doc_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def create_document(self, doc_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new knowledge base document.
        
        Args:
            doc_data: Document data
            
        Returns:
            Document ID if successful
        """
        try:
            doc_data["created_at"] = datetime.now(timezone.utc)
            doc_data["updated_at"] = datetime.now(timezone.utc)
            doc_data["published"] = doc_data.get("published", True)
            
            doc_ref = self.collection.add(doc_data)
            doc_id = doc_ref[1].id
            
            logger.info(f"Created knowledge document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return None
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a knowledge base document.
        
        Args:
            doc_id: Document ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            updates["updated_at"] = datetime.now(timezone.utc)
            self.collection.document(doc_id).update(updates)
            
            logger.info(f"Updated knowledge document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a knowledge base document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            self.collection.document(doc_id).delete()
            logger.info(f"Deleted knowledge document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def _calculate_relevance_score(self, query: str, doc: Dict[str, Any]) -> float:
        """
        Calculate relevance score between query and document.
        
        Simple keyword matching for now.
        Future: Can use embeddings for semantic similarity.
        
        Args:
            query: Search query
            doc: Document data
            
        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()
        score = 0.0
        
        # Check title (higher weight)
        title = doc.get("title", "").lower()
        if query_lower in title:
            score += 0.5
        
        # Check content
        content = doc.get("content", "").lower()
        if query_lower in content:
            score += 0.3
        
        # Check tags
        tags = doc.get("tags", [])
        for tag in tags:
            if query_lower in tag.lower():
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def seed_initial_data(self):
        """
        Seed initial knowledge base data.
        
        Creates sample documents for services, pricing, team, and FAQs.
        """
        initial_docs = [
            # Services
            {
                "category": "services",
                "title": "AI Integration Services",
                "content": """We offer custom AI solutions tailored to your business needs. Our AI Integration service includes:

- Custom AI model development and training
- Integration with existing systems
- API development and deployment
- Ongoing maintenance and optimization
- Training and support for your team

Perfect for businesses looking to leverage AI for automation, insights, and competitive advantage.""",
                "tags": ["ai", "integration", "services", "machine learning"],
                "order": 1,
                "published": True
            },
            {
                "category": "services",
                "title": "Data Analytics",
                "content": """Transform your data into actionable insights with our Data Analytics services:

- Data pipeline development
- Business intelligence dashboards
- Predictive analytics
- Real-time data processing
- Custom reporting solutions

We help you make data-driven decisions with confidence.""",
                "tags": ["data", "analytics", "insights", "business intelligence"],
                "order": 2,
                "published": True
            },
            {
                "category": "services",
                "title": "Cloud Migration",
                "content": """Seamless transition to cloud infrastructure with our Cloud Migration services:

- Cloud strategy and planning
- Infrastructure as Code (IaC)
- Migration execution
- Security and compliance
- Cost optimization

We support AWS, Google Cloud, and Azure migrations.""",
                "tags": ["cloud", "migration", "aws", "gcp", "azure"],
                "order": 3,
                "published": True
            },
            
            # Pricing
            {
                "category": "pricing",
                "title": "AI Integration Pricing",
                "content": """Our AI Integration packages start at $5,000/month and include:

**Starter Package** - $5,000/month
- Basic AI model integration
- Up to 2 models
- Standard support

**Professional Package** - $10,000/month
- Advanced AI solutions
- Up to 5 models
- Priority support
- Monthly optimization

**Enterprise Package** - Custom pricing
- Unlimited models
- Dedicated team
- 24/7 support
- Custom SLAs

All packages include initial consultation and setup. Contact us for a custom quote.""",
                "tags": ["pricing", "ai", "cost", "packages"],
                "order": 1,
                "published": True
            },
            
            # Team
            {
                "category": "team",
                "title": "Our Expertise",
                "content": """MLGround is powered by a team of experienced AI and data professionals:

- 10+ years combined experience in AI/ML
- Former engineers from Google, Microsoft, and Amazon
- PhDs in Computer Science and Machine Learning
- Published researchers in top AI conferences
- Proven track record with 50+ successful projects

We're passionate about making AI accessible and impactful for businesses of all sizes.""",
                "tags": ["team", "expertise", "experience"],
                "order": 1,
                "published": True
            },
            
            # FAQs
            {
                "category": "faq",
                "title": "How long does implementation take?",
                "content": """Implementation timelines vary based on complexity:

- Basic AI Integration: 4-6 weeks
- Data Analytics Dashboard: 2-4 weeks
- Cloud Migration: 6-12 weeks
- Enterprise Solutions: 3-6 months

We provide detailed timelines during the consultation phase and keep you updated throughout the project.""",
                "tags": ["timeline", "implementation", "duration"],
                "order": 1,
                "published": True
            },
            {
                "category": "faq",
                "title": "Do you offer ongoing support?",
                "content": """Yes! We offer comprehensive ongoing support:

- 24/7 technical support (Enterprise)
- Regular maintenance and updates
- Performance monitoring
- Model retraining and optimization
- Training for your team
- Quarterly business reviews

Support levels vary by package. All clients receive at least standard business hours support.""",
                "tags": ["support", "maintenance", "help"],
                "order": 2,
                "published": True
            },
            {
                "category": "faq",
                "title": "What industries do you serve?",
                "content": """We work with diverse industries including:

- Healthcare and Life Sciences
- Financial Services
- Retail and E-commerce
- Manufacturing
- Technology and SaaS
- Professional Services

Our solutions are customized to meet industry-specific requirements and compliance needs.""",
                "tags": ["industries", "sectors", "verticals"],
                "order": 3,
                "published": True
            },
            
            # Policies
            {
                "category": "policies",
                "title": "Refund Policy",
                "content": """We stand behind our work with a fair refund policy:

- 30-day money-back guarantee on initial consultation
- Prorated refunds for monthly services (if cancelled within first 30 days)
- Custom projects: Milestone-based payments with satisfaction guarantees
- No refunds on completed work

For enterprise contracts, refund terms are outlined in the service agreement.""",
                "tags": ["refund", "policy", "guarantee"],
                "order": 1,
                "published": True
            },
            {
                "category": "policies",
                "title": "Privacy Policy",
                "content": """Your data privacy is our priority:

- We never share your data with third parties
- All data is encrypted at rest and in transit
- Compliance with GDPR, CCPA, and HIPAA (when applicable)
- Regular security audits
- Data retention policies customizable per client

You retain full ownership of your data and models.""",
                "tags": ["privacy", "security", "data protection"],
                "order": 2,
                "published": True
            }
        ]
        
        try:
            for doc_data in initial_docs:
                self.create_document(doc_data)
            
            logger.info(f"Seeded {len(initial_docs)} initial knowledge documents")
            return True
            
        except Exception as e:
            logger.error(f"Error seeding initial data: {e}")
            return False
