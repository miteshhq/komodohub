from app import app, db
from models import Species, EducationalResource, ConservationProgram, User, ResourceTag # Added ResourceTag import
from datetime import datetime, timedelta
import os

def init_data():
    # Check and create users separately
    teacher = User.query.filter_by(email="teacher@komodohub.org").first()
    if not teacher:
        teacher = User(
            username="DefaultTeacher",
            email="teacher@komodohub.org",
            role="teacher"
        )
        teacher.set_password("password123")
        db.session.add(teacher)
        
    # Create student separately
    student = User.query.filter_by(email="student@komodohub.org").first()
    if not student:
        student = User(
            username="TestStudent",
            email="student@komodohub.org",
            role="student"
        )
        student.set_password("password123")
        db.session.add(student)

    # Create member separately
    member = User.query.filter_by(email="member@komodohub.org").first()
    if not member:
        member = User(
            username="TestMember",
            email="member@komodohub.org",
            role="member"
        )
        member.set_password("password123")
        db.session.add(member)

    # Create admin separately
    admin = User.query.filter_by(email="admin@komodohub.org").first()
    if not admin:
        admin = User(
            username="Admin",
            email="admin@komodohub.org",
            role="admin"
        )
        adminPass = os.environ.get("ADMIN_PASS")
        admin.set_password(adminPass)
        db.session.add(admin)

    # Commit all user changes
    db.session.commit()

    # Create default tags
    tag_names = [
        "Conservation", "Wildlife", "Education", "Research",
        "Marine Life", "Forest", "Climate Change", "Community",
        "Sustainability", "Biodiversity"
    ]

    tags = {}
    for tag_name in tag_names:
        tag = ResourceTag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = ResourceTag(name=tag_name)
            db.session.add(tag)
        tags[tag_name] = tag

    db.session.commit()

    # Add endangered species
    species_data = [
        {
            "name": "Sumatran Tiger",
            "scientific_name": "Panthera tigris sumatrae",
            "description": "The Sumatran tiger is the smallest of all tiger species and is native to the Indonesian island of Sumatra. They are critically endangered due to habitat loss and poaching.",
            "population": 400,
            "conservation_status": "Critically Endangered",
            "habitat": "Tropical forests of Sumatra",
            "threats": "Habitat loss due to deforestation, human-wildlife conflict, and poaching"
        },
        {
            "name": "Javan Rhinoceros",
            "scientific_name": "Rhinoceros sondaicus",
            "description": "The Javan rhinoceros is one of the rarest large mammals on Earth. They are found only in Ujung Kulon National Park in Java, Indonesia.",
            "population": 74,
            "conservation_status": "Critically Endangered",
            "habitat": "Tropical rainforests",
            "threats": "Limited genetic diversity, natural disasters, and human encroachment"
        },
        {
            "name": "Bali Myna",
            "scientific_name": "Leucopsar rothschildi",
            "description": "The Bali Myna is a critically endangered bird endemic to Bali. Known for its pure white plumage and blue mask, it is Bali's official mascot.",
            "population": 100,
            "conservation_status": "Critically Endangered",
            "habitat": "Tropical forests of Bali",
            "threats": "Illegal capture for pet trade and habitat loss"
        },
        {
            "name": "Komodo Dragon",
            "scientific_name": "Varanus komodoensis",
            "description": "The Komodo dragon is the largest living lizard species, found in several islands in Indonesia. They are known for their size and hunting abilities.",
            "population": 3000,
            "conservation_status": "Endangered",
            "habitat": "Grasslands and forests of Komodo Island",
            "threats": "Limited habitat range and human activities"
        },
        {
            "name": "Orangutan",
            "scientific_name": "Pongo abelii",
            "description": "Sumatran orangutans are critically endangered great apes found only in the northern parts of Sumatra, Indonesia.",
            "population": 14000,
            "conservation_status": "Critically Endangered",
            "habitat": "Tropical rainforest",
            "threats": "Deforestation and illegal pet trade"
        },
        {
            "name": "Proboscis Monkey",
            "scientific_name": "Nasalis larvatus",
            "description": "Known for its distinctive nose, this endangered primate is endemic to Borneo. They play a crucial role in seed dispersal and forest regeneration.",
            "population": 7000,
            "conservation_status": "Endangered",
            "habitat": "Mangrove forests and swamps",
            "threats": "Habitat fragmentation and hunting"
        },
        {
            "name": "Sunda Pangolin",
            "scientific_name": "Manis javanica",
            "description": "This unique scaled mammal is heavily trafficked for its meat and scales, used in traditional medicine.",
            "population": None,  # Changed from "Unknown" to None
            "conservation_status": "Critically Endangered",
            "habitat": "Primary and secondary forests",
            "threats": "Poaching and illegal wildlife trade"
        },
        {
            "name": "Hawksbill Sea Turtle",
            "scientific_name": "Eretmochelys imbricata",
            "description": "These sea turtles are essential for maintaining the health of coral reefs. They are extensively hunted for their beautiful shell.",
            "population": None, # Changed from "Unknown" to None
            "conservation_status": "Critically Endangered",
            "habitat": "Coral reefs and coastal waters",
            "threats": "Poaching, habitat destruction, and climate change"
        },
        {
            "name": "Sulawesi Black Macaque",
            "scientific_name": "Macaca nigra",
            "description": "These social primates are known for their jet-black fur and unique culture. They face multiple threats in their native habitat.",
            "population": 5000,
            "conservation_status": "Critically Endangered",
            "habitat": "Tropical rainforests of Sulawesi",
            "threats": "Hunting for bushmeat and habitat loss"
        },
        {
            "name": "Sumatran Elephant",
            "scientific_name": "Elephas maximus sumatranus",
            "description": "A subspecies of the Asian elephant native to Sumatra, known for their smaller size and unique behaviors.",
            "population": 2400,
            "conservation_status": "Critically Endangered",
            "habitat": "Lowland tropical forests",
            "threats": "Human-elephant conflict and habitat fragmentation"
        },
        {
            "name": "Clouded Leopard",
            "scientific_name": "Neofelis diardi",
            "description": "These elusive cats are excellent climbers and are rarely seen in the wild. They are threatened by deforestation.",
            "population": None, # Changed from "Unknown" to None
            "conservation_status": "Vulnerable",
            "habitat": "Primary and secondary forests",
            "threats": "Habitat loss and poaching"
        },
        {
            "name": "Green Sea Turtle",
            "scientific_name": "Chelonia mydas",
            "description": "These magnificent sea turtles are vital for maintaining seagrass ecosystems and are found throughout Indonesian waters.",
            "population": None, # Changed from "Unknown" to None
            "conservation_status": "Endangered",
            "habitat": "Tropical and subtropical oceans",
            "threats": "Plastic pollution and climate change"
        }
    ]

    # Add education resources
    education_data = [
        {
            "title": "Understanding Indonesian Wildlife",
            "content": "A comprehensive guide to Indonesia's unique biodiversity and the importance of conservation efforts. Learn about the various ecosystems and their inhabitants.",
            "author_id": teacher.id,
            "tags": [tags["Wildlife"], tags["Education"], tags["Biodiversity"]]
        },
        {
            "title": "Conservation Success Stories",
            "content": "Learn about successful conservation projects in Indonesia and how they've helped protect endangered species. From community initiatives to national programs.",
            "author_id": teacher.id,
            "tags": [tags["Conservation"], tags["Community"]]
        },
        {
            "title": "Guide to Wildlife Photography",
            "content": "Tips and techniques for photographing wildlife responsibly while maintaining a safe distance. Includes ethical guidelines and best practices.",
            "author_id": teacher.id,
            "tags": [tags["Wildlife"], tags["Education"]]
        },
        {
            "title": "Marine Conservation Initiatives",
            "content": "Discover the efforts to protect Indonesia's marine life and coral reefs. Including sea turtle conservation programs and reef restoration projects.",
            "author_id": teacher.id,
            "tags": [tags["Marine Life"], tags["Conservation"]]
        },
        {
            "title": "Traditional Knowledge in Conservation",
            "content": "How indigenous knowledge and practices contribute to wildlife conservation in Indonesia. Learn about sustainable resource management techniques.",
            "author_id": teacher.id,
            "tags": [tags["Community"], tags["Sustainability"]]
        },
        {
            "title": "Climate Change Impact on Wildlife",
            "content": "Understanding how climate change affects Indonesian wildlife and their habitats. Includes adaptation strategies and conservation approaches.",
            "author_id": teacher.id,
            "tags": [tags["Climate Change"], tags["Research"]]
        },
        {
            "title": "Wildlife Rehabilitation",
            "content": "Learn about the process of rehabilitating injured or orphaned wildlife and preparing them for release back into their natural habitats.",
            "author_id": teacher.id,
            "tags": [tags["Wildlife"], tags["Conservation"]]
        },
        {
            "title": "Citizen Science in Conservation",
            "content": "How everyday citizens can contribute to wildlife conservation through observation, data collection, and community engagement.",
            "author_id": teacher.id,
            "tags": [tags["Community"], tags["Research"], tags["Education"]]
        },
        {
            "title": "Sustainable Tourism Practices",
            "content": "Guidelines for responsible wildlife tourism that benefits both local communities and conservation efforts.",
            "author_id": teacher.id,
            "tags": [tags["Sustainability"], tags["Community"]]
        },
        {
            "title": "Understanding Animal Behavior",
            "content": "An introduction to wildlife behavior and its importance in conservation planning and management.",
            "author_id": teacher.id,
            "tags": [tags["Wildlife"], tags["Research"], tags["Education"]]
        }
    ]

    # Add conservation programs
    program_data = [
        {
            "title": "Tiger Protection Program",
            "description": "A comprehensive program to protect Sumatran tigers through habitat preservation and anti-poaching measures.",
            "location": "Sumatra",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=365),
            "coordinator_id": teacher.id
        },
        {
            "title": "Bali Myna Breeding Program",
            "description": "A breeding and release program to increase the wild population of Bali Mynas.",
            "location": "Bali",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=730),
            "coordinator_id": teacher.id
        },
        {
            "title": "Rainforest Protection Initiative",
            "description": "Working with local communities to protect and restore rainforest habitats.",
            "location": "Various locations",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=365),
            "coordinator_id": teacher.id
        },
        {
            "title": "Marine Turtle Conservation",
            "description": "Protecting nesting sites and monitoring sea turtle populations along Indonesia's coastlines.",
            "location": "Coastal regions",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=365),
            "coordinator_id": teacher.id
        },
        {
            "title": "Pangolin Rescue and Rehabilitation",
            "description": "Rescuing confiscated pangolins and preparing them for release back into the wild.",
            "location": "Java",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=180),
            "coordinator_id": teacher.id
        },
        {
            "title": "Elephant Conservation Project",
            "description": "Reducing human-elephant conflict through community outreach and habitat protection.",
            "location": "Sumatra",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=365),
            "coordinator_id": teacher.id
        },
        {
            "title": "Coral Reef Restoration",
            "description": "Rehabilitating damaged coral reefs and establishing marine protected areas.",
            "location": "Raja Ampat",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=730),
            "coordinator_id": teacher.id
        },
        {
            "title": "Wildlife Corridor Development",
            "description": "Creating and protecting wildlife corridors to connect fragmented habitats.",
            "location": "Kalimantan",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=548),
            "coordinator_id": teacher.id
        },
        {
            "title": "Community-Based Conservation",
            "description": "Empowering local communities to protect their natural resources and wildlife.",
            "location": "Sulawesi",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=365),
            "coordinator_id": teacher.id
        },
        {
            "title": "Mangrove Restoration Project",
            "description": "Restoring mangrove ecosystems to protect coastlines and marine life.",
            "location": "Papua",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=730),
            "coordinator_id": teacher.id
        }
    ]

    # Add data to database
    for species in species_data:
        if not Species.query.filter_by(name=species['name']).first():
            db.session.add(Species(**species))

    for resource in education_data:
        tags_to_add = resource.pop('tags')  # Remove tags from the dict
        if not EducationalResource.query.filter_by(title=resource['title']).first():
            new_resource = EducationalResource(**resource)
            new_resource.tags.extend(tags_to_add)
            db.session.add(new_resource)

    for program in program_data:
        if not ConservationProgram.query.filter_by(title=program['title']).first():
            db.session.add(ConservationProgram(**program))

    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        init_data()