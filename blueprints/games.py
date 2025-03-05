from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user
from models import Species, EducationalResource, GameChallenge, UserChallenge
from app import db
import random
import logging

games = Blueprint('games', __name__)

@games.route('/quiz/species')
@login_required
def species_quiz():
    species = Species.query.all()
    return render_template('games/species_quiz.html', species=species)

@games.route('/quiz/conservation')
@login_required
def conservation_quiz():
    resources = EducationalResource.query.all()
    return render_template('games/conservation_quiz.html', resources=resources)

@games.route('/games/habitat-explorer')
@login_required
def habitat_explorer():
    species = Species.query.all()
    return render_template('games/habitat_explorer.html', species=species)

@games.route('/api/quiz/get-question')
@login_required
def get_quiz_question():
    try:
        current_app.logger.debug("Fetching quiz question")
        species = Species.query.all()

        if not species:
            current_app.logger.error("No species found in database")
            return jsonify({"error": "No species data available"}), 500

        # Basic question about conservation status
        species_list = random.sample(species, min(4, len(species)))
        correct_species = random.choice(species_list)

        options = [s.name for s in species_list]
        correct_index = options.index(correct_species.name)

        # Create or update user challenge
        challenge = UserChallenge.query.filter_by(
            user_id=current_user.id,
            status='in_progress'
        ).first()

        if not challenge:
            game_challenge = GameChallenge.query.filter_by(
                is_active=True
            ).first()

            if game_challenge:
                challenge = UserChallenge(
                    user_id=current_user.id,
                    challenge_id=game_challenge.id
                )
                db.session.add(challenge)
                db.session.commit()

        return jsonify({
            "question": f"What is the conservation status of the {correct_species.name}?",
            "options": options,
            "correct": correct_index,
            "explanation": f"The {correct_species.name} is {correct_species.conservation_status} with a population of {correct_species.population or 'unknown'} individuals.",
            "points": 10  # Points for correct answer
        })
    except Exception as e:
        current_app.logger.error(f"Error generating quiz question: {str(e)}")
        return jsonify({"error": "Failed to generate question"}), 500

@games.route('/api/conservation-quiz/get-question')
@login_required
def get_conservation_question():
    try:
        current_app.logger.debug("Fetching conservation quiz question")
        resources = EducationalResource.query.all()

        if not resources:
            current_app.logger.error("No educational resources found in database")
            return jsonify({"error": "No educational content available"}), 500

        # Get a random resource and create a question about it
        resource = random.choice(resources)

        # Generate 3 random incorrect options from other resources' titles
        other_resources = [r for r in resources if r.id != resource.id]
        wrong_options = random.sample([r.title for r in other_resources], min(3, len(other_resources)))

        # Create options list with correct answer at random position
        options = wrong_options + [resource.title]
        random.shuffle(options)
        correct_index = options.index(resource.title)

        # Create question types
        question_types = [
            f"Which conservation initiative focuses on {resource.title.lower()}?",
            f"Which of the following educational resources discusses {resource.title.lower()}?",
            f"Which conservation program addresses {resource.title.lower()}?"
        ]

        # Track progress in UserChallenge
        challenge = UserChallenge.query.filter_by(
            user_id=current_user.id,
            status='in_progress'
        ).first()

        if not challenge:
            game_challenge = GameChallenge.query.filter_by(
                is_active=True
            ).first()

            if game_challenge:
                challenge = UserChallenge(
                    user_id=current_user.id,
                    challenge_id=game_challenge.id
                )
                db.session.add(challenge)
                db.session.commit()

        return jsonify({
            "question": random.choice(question_types),
            "options": options,
            "correct": correct_index,
            "explanation": resource.content[:200] + "...",  # First 200 characters of content as explanation
            "points": 15  # Higher points for conservation knowledge
        })
    except Exception as e:
        current_app.logger.error(f"Error generating conservation question: {str(e)}")
        return jsonify({"error": "Failed to generate question"}), 500