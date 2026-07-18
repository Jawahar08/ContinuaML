import json
from sqlmodel import Session, select
from app.db import engine, init_db
from app.auth import get_password_hash
from app.models import (
    User, Workspace, Membership, WorkspaceRole, Model, ModelVersion,
    Dataset, DatasetVersion, PreprocessingRecipe, ContinualLearningStrategy,
    BenchmarkTask, BenchmarkProtocol, ResearchPlan, TrainingConfig,
    Experiment, ProvenanceStatus
)

def seed_database():
    init_db()
    with Session(engine) as session:
        # 1. Create Default User
        admin_email = "admin@continuaml.com"

        existing_user = session.exec(select(User).where(User.email == admin_email)).first()
        if not existing_user:
            user = User(
                email=admin_email,
                hashed_password=get_password_hash("AdminPass123!"),
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            user = existing_user

        # 2. Create Default Workspace
        ws_id = "workspace_default"
        existing_ws = session.exec(select(Workspace).where(Workspace.id == ws_id)).first()
        if not existing_ws:
            ws = Workspace(id=ws_id, name="Default Research Workspace")
            session.add(ws)
            
            # Workspace membership
            membership = Membership(
                user_id=user.id,
                workspace_id=ws_id,
                role=WorkspaceRole.ADMIN
            )
            session.add(membership)
            session.commit()
        else:
            ws = existing_ws

        # 3. Seed Models
        models_data = [
            ("tinyllama-1.1b", "TinyLlama", "LlamaForCausalLM", 1100000000, 2048, "Apache-2.0", "HuggingFace"),
            ("phi-2", "Phi-2", "MixformerSequential", 2700000000, 2048, "MIT", "HuggingFace")
        ]
        for m_id, name, arch, params, ctx, lic, src in models_data:
            existing_model = session.exec(select(Model).where(Model.id == m_id)).first()
            if not existing_model:
                model = Model(
                    id=m_id, workspace_id=ws_id, name=name, architecture=arch,
                    param_count=params, context_length=ctx, license=lic, source=src
                )
                session.add(model)
                version = ModelVersion(
                    id=f"{m_id}-v1", model_id=m_id, version="1.0.0", download_status="ready"
                )
                session.add(version)
        session.commit()

        # 4. Seed Datasets
        datasets_data = [
            ("dataset_triviaqa", "TriviaQA", "HuggingFace trivia_qa", "Apache-2.0"),
            ("dataset_gsm8k", "GSM8K", "HuggingFace gsm8k", "MIT")
        ]
        for d_id, name, src, lic in datasets_data:
            existing_ds = session.exec(select(Dataset).where(Dataset.id == d_id)).first()
            if not existing_ds:
                ds = Dataset(
                    id=d_id, workspace_id=ws_id, name=name, source=src, license=lic
                )
                session.add(ds)
                version = DatasetVersion(
                    id=f"{d_id}-v1", dataset_id=d_id, version="1.0", status=ProvenanceStatus.REAL
                )
                session.add(version)
        session.commit()

        # 5. Seed Preprocessing Recipes
        recipe_name = "default_norm_recipe"
        existing_recipe = session.exec(select(PreprocessingRecipe).where(PreprocessingRecipe.name == recipe_name)).first()
        if not existing_recipe:
            recipe = PreprocessingRecipe(
                id="recipe-default",
                workspace_id=ws_id,
                name=recipe_name,
                recipe_json=b'{"lowercase": true, "remove_special_chars": false}'
            )
            session.add(recipe)
            session.commit()

        # 6. Seed Continual Learning Strategies
        strategies = [
            ("ewc", "Elastic Weight Consolidation (EWC)", "EWC uses Fisher Information matrix to slow down update on important weights.", "Kirkpatrick et al., 2017"),
            ("experience_replay", "Experience Replay", "Replay stored samples of old tasks during training.", "Robins, 1995"),
            ("finetune_baseline", "Fine-Tuning Baseline", "Direct sequential fine-tuning without forgetting mitigation.", "N/A")
        ]
        for s_id, name, desc, cite in strategies:
            existing_strat = session.exec(select(ContinualLearningStrategy).where(ContinualLearningStrategy.id == s_id)).first()
            if not existing_strat:
                strat = ContinualLearningStrategy(id=s_id, name=name, description=desc, citation=cite)
                session.add(strat)
        session.commit()

        # 7. Seed Benchmark Tasks & Protocols
        task_data = [
            ("task_triviaqa", "TriviaQA Bench", "dataset_triviaqa-v1", "accuracy"),
            ("task_gsm8k", "GSM8K Math Bench", "dataset_gsm8k-v1", "accuracy")
        ]
        for t_id, name, ds_ver, m_type in task_data:
            existing_task = session.exec(select(BenchmarkTask).where(BenchmarkTask.id == t_id)).first()
            if not existing_task:
                task = BenchmarkTask(id=t_id, name=name, dataset_version_id=ds_ver, metric_type=m_type)
                session.add(task)
        session.commit()

        existing_protocol = session.exec(select(BenchmarkProtocol).where(BenchmarkProtocol.name == "Standard Sequence")).first()
        if not existing_protocol:
            protocol = BenchmarkProtocol(
                id="proto_standard",
                workspace_id=ws_id,
                name="Standard Sequence",
                tasks_order_json=b'["task_triviaqa", "task_gsm8k"]'
            )
            session.add(protocol)
            session.commit()

        # 8. Seed Training Config
        existing_cfg = session.exec(select(TrainingConfig).where(TrainingConfig.id == "cfg_default")).first()
        if not existing_cfg:
            cfg = TrainingConfig(
                id="cfg_default",
                workspace_id=ws_id,
                hyperparams_json=b'{"learning_rate": 5e-5, "batch_size": 8, "epochs": 3}'
            )
            session.add(cfg)
            session.commit()

        print("Database seeded successfully with DEMO & baseline values.")

if __name__ == "__main__":
    seed_database()
