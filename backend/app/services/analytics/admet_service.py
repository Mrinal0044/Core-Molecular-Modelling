import traceback
import logging

logger = logging.getLogger(__name__)

class AdmetService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                from admet_ai import ADMETModel
                logger.info("Initializing ADMETModel (this may take a moment)...")
                cls._model = ADMETModel()
            except ImportError:
                logger.error("admet_ai package is not installed.")
                return None
        return cls._model

    @classmethod
    def predict(cls, smiles: str) -> dict:
        """
        Predict ADMET properties for a single SMILES string or compound name.
        Returns a dictionary of properties or an error dict.
        """
        try:
            from rdkit import Chem
            import pubchempy as pcp
            
            # Check if input is a valid SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.info(f"'{smiles}' is not a valid SMILES. Resolving via PubChem...")
                compounds = pcp.get_compounds(smiles, 'name')
                if not compounds:
                    return {"error": f"Could not resolve '{smiles}' to a valid structure."}
                smiles = compounds[0].canonical_smiles or compounds[0].isomeric_smiles
                logger.info(f"Resolved to SMILES: {smiles}")
            model = cls.get_model()
            if model is None:
                return {"error": "ADMETModel could not be initialized (missing dependency)."}
            
            pred_df = model.predict([smiles])
            if pred_df is None or pred_df.empty:
                return {"error": "No ADMET data generated."}
                
            # Convert first row to a dict
            result_dict = pred_df.iloc[0].to_dict()
            return result_dict
        except Exception as e:
            logger.error(f"ADMET prediction failed for {smiles}: {e}")
            traceback.print_exc()
            return {"error": str(e)}
