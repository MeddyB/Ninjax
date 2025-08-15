"""
Script principal pour exécuter tous les tests du projet
"""
import sys
import subprocess
import os
import time
from pathlib import Path
import argparse


def run_command(command, timeout=300):
    """Exécute une commande avec timeout"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def run_test_category(category_name, test_paths, verbose=False):
    """Exécute une catégorie de tests"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTS {category_name.upper()}")
    print(f"{'='*60}")
    
    total_passed = 0
    total_failed = 0
    total_time = 0
    
    for test_path in test_paths:
        if not os.path.exists(test_path):
            print(f"⚠️  Fichier de test non trouvé: {test_path}")
            continue
        
        print(f"\n📋 Exécution: {test_path}")
        print("-" * 40)
        
        start_time = time.time()
        
        # Construire la commande pytest
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v" if verbose else "-q",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ]
        
        success, stdout, stderr = run_command(" ".join(cmd))
        
        end_time = time.time()
        test_time = end_time - start_time
        total_time += test_time
        
        if success:
            # Extraire les statistiques des tests
            lines = stdout.split('\n')
            summary_lines = [line for line in lines if 'passed' in line and ('failed' in line or 'error' in line or line.strip().endswith('passed'))]
            
            if summary_lines:
                summary = summary_lines[-1].strip()
                print(f"✅ {summary} ({test_time:.1f}s)")
                
                # Essayer d'extraire le nombre de tests passés
                try:
                    if 'passed' in summary:
                        passed_count = int(summary.split()[0])
                        total_passed += passed_count
                except:
                    total_passed += 1
            else:
                print(f"✅ Tests passés ({test_time:.1f}s)")
                total_passed += 1
        else:
            print(f"❌ Échec des tests ({test_time:.1f}s)")
            total_failed += 1
            
            if verbose and stdout:
                print("Sortie:", stdout[-500:])
            if stderr:
                print("Erreur:", stderr[-300:])
    
    print(f"\n📊 Résumé {category_name}:")
    print(f"   ✅ Tests passés: {total_passed}")
    print(f"   ❌ Tests échoués: {total_failed}")
    print(f"   ⏱️  Temps total: {total_time:.1f}s")
    
    return total_passed, total_failed, total_time


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Exécute tous les tests du projet Axiom Trade")
    parser.add_argument("--category", "-c", 
                       choices=["unit", "integration", "migration", "all"],
                       default="all",
                       help="Catégorie de tests à exécuter")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Mode verbose")
    parser.add_argument("--fast", "-f", action="store_true",
                       help="Mode rapide (skip les tests lents)")
    
    args = parser.parse_args()
    
    print("🚀 EXÉCUTION DES TESTS AXIOM TRADE")
    print("=" * 60)
    print(f"Mode: {'Verbose' if args.verbose else 'Standard'}")
    print(f"Catégorie: {args.category}")
    if args.fast:
        print("⚡ Mode rapide activé")
    
    # Définir les catégories de tests
    test_categories = {
        "unit": {
            "name": "Tests Unitaires",
            "paths": [
                "tests/test_services/test_token_service.py",
                "tests/test_services/test_windows_service.py",
                "tests/test_services/test_api_proxy_service.py",
                "tests/test_data_models/test_token_model.py",
                "tests/test_data_models/test_service_model.py",
                "tests/test_utils/test_file_utils.py",
                "tests/test_utils/test_validation.py",
                "tests/test_core/test_config.py"
            ]
        },
        "integration": {
            "name": "Tests d'Intégration",
            "paths": [
                "tests/integration/test_backend_api.py",
                "tests/integration/test_multi_app_communication.py",
                "tests/integration/test_extension_backend.py"
            ]
        },
        "migration": {
            "name": "Tests de Migration",
            "paths": [
                "tests/migration/test_backward_compatibility.py",
                "tests/migration/test_windows_service_migration.py"
            ]
        }
    }
    
    # Exécuter les tests selon la catégorie choisie
    total_passed = 0
    total_failed = 0
    total_time = 0
    
    categories_to_run = []
    if args.category == "all":
        categories_to_run = ["unit", "integration", "migration"]
    else:
        categories_to_run = [args.category]
    
    for category in categories_to_run:
        if category in test_categories:
            category_info = test_categories[category]
            
            # Filtrer les tests lents en mode rapide
            test_paths = category_info["paths"]
            if args.fast and category == "integration":
                # En mode rapide, skip certains tests d'intégration longs
                test_paths = [p for p in test_paths if "multi_app" not in p]
            
            passed, failed, test_time = run_test_category(
                category_info["name"],
                test_paths,
                args.verbose
            )
            
            total_passed += passed
            total_failed += failed
            total_time += test_time
    
    # Résumé final
    print(f"\n{'='*60}")
    print("📈 RÉSUMÉ FINAL")
    print(f"{'='*60}")
    print(f"✅ Total tests passés: {total_passed}")
    print(f"❌ Total tests échoués: {total_failed}")
    print(f"⏱️  Temps total: {total_time:.1f}s")
    
    if total_failed == 0:
        print("🎉 Tous les tests sont passés!")
        success_rate = 100.0
    else:
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        print(f"⚠️  Certains tests ont échoué")
    
    print(f"📊 Taux de réussite: {success_rate:.1f}%")
    
    # Recommandations
    if success_rate < 80:
        print("\n🔧 RECOMMANDATIONS:")
        print("   - Vérifiez les dépendances manquantes")
        print("   - Exécutez les tests en mode verbose (-v) pour plus de détails")
        print("   - Vérifiez la configuration de l'environnement de test")
    elif success_rate < 95:
        print("\n💡 SUGGESTIONS:")
        print("   - Quelques tests échouent, vérifiez les logs détaillés")
        print("   - Certains tests peuvent nécessiter des permissions spéciales")
    
    # Code de sortie
    exit_code = 0 if total_failed == 0 else 1
    
    if args.category == "all":
        print(f"\n🏁 Tests terminés avec le code de sortie: {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()