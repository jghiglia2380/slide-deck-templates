#!/usr/bin/env python3
"""
Multi-State Resource Generator for PFL Academy

Processes the 181 free-PDF resources for every state that has a canonical
state-data/states/{state}.json (36 today) with:
  * FEDERAL figure currency from state-data/federal/federal_figures.json (single source)
  * STATE figure resolution from state-data/states/{state}.json (per-state)
  * null backing field -> visible flagged placeholder (never an Oklahoma value, never a guess)

This replaces the previous cosmetic behaviour, where sanitize_html_content() only swapped
title/header/footer branding and left every figure as-is. See figure_resolver.py for the
resolution engine and docs/TOKEN_MAP.md for the token vocabulary.

Ground-truth note (verified 2026-07-24): the oklahoma-free-resources/ templates are
generic/national content — they contain NO baked Oklahoma STATE figures, so there is no
Oklahoma-figure "bleed" to substitute out. The real, resolvable currency defect is baked
old-year FEDERAL literals (2022/2023/2024 standard deductions, brackets, retirement limits)
that survive into every state's output. This generator fixes those; the STATE resolver is
ready for when the templates are tokenized (a separate content task).

Modes:
  python3 generate_state_resources.py --dry-run [--states nc ky tx]
        Figure resolution + report only. NO Anthropic API needed. Writes localized HTML to
        free-resources-dryrun/ and prints the currency report. This is the verifiable slice.
  python3 generate_state_resources.py --full
        Full pipeline incl. AI standards-mapping (needs ANTHROPIC_API_KEY).
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
import time
import logging

import figure_resolver as fr

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StateResourceGenerator:
    def __init__(self, output_base_dir=None):
        # Repo-relative paths (the previous absolute /Users/justin/pfl-academy/... paths do
        # not exist under the iCloud checkout).
        self.base_oklahoma_dir = fr.OKLAHOMA_SOURCE
        self.output_base_dir = Path(output_base_dir) if output_base_dir \
            else (fr.REPO_ROOT / "free-resources")
        self.state_alignments_dir = fr.REPO_ROOT / "State-Alignments"
        self.output_base_dir.mkdir(exist_ok=True, parents=True)

        # Single source of federal figures.
        self.federal = fr.load_federal()

        # State list is DATA-DRIVEN: every state with a canonical {state}.json (36 today).
        # The old hardcoded 37-name list + skip_states (which dropped it to ~28 by skipping
        # "already-processed" states) is gone — those states carried the same stale federal
        # figures and must be reprocessed. Oklahoma is included (identity source is valid).
        self.state_slugs = fr.list_state_slugs()

        self._client = None  # lazy: only built for the AI standards-mapping (--full)

    # ------------------------------------------------------------------
    # State-data helpers
    # ------------------------------------------------------------------
    def state_name_to_slug(self, state_name):
        return state_name.lower().replace(" ", "-")

    @property
    def client(self):
        if self._client is None:
            import anthropic
            from dotenv import load_dotenv
            load_dotenv()
            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError("ANTHROPIC_API_KEY not set — needed only for --full "
                                   "(AI standards-mapping). Use --dry-run to skip it.")
            self._client = anthropic.Anthropic(api_key=key)
        return self._client

    def get_state_alignment_content(self, state_name):
        """Extract standards alignment from state directory."""
        state_dir = self.state_alignments_dir / state_name
        
        if not state_dir.exists():
            logger.warning(f"State directory not found: {state_dir}")
            return None
        
        # Look for HTML or MD files with alignment info
        alignment_files = list(state_dir.glob("*.html")) + list(state_dir.glob("*.md"))
        
        if not alignment_files:
            logger.warning(f"No alignment files found for {state_name}")
            return None
        
        # Read the first alignment file found
        alignment_file = alignment_files[0]
        try:
            with open(alignment_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded alignment content for {state_name} from {alignment_file.name}")
            return content
        except Exception as e:
            logger.error(f"Error reading alignment file for {state_name}: {e}")
            return None
    
    def extract_standards_mapping(self, state_name, alignment_content):
        """Use Claude to extract standards mapping from alignment content."""
        
        prompt = f"""
        Analyze this {state_name} financial literacy standards alignment document and extract the key standards organization.
        
        Create a JSON mapping that organizes financial literacy topics into {state_name}'s specific standards structure.
        
        Return ONLY a valid JSON object with this structure:
        {{
            "state_name": "{state_name}",
            "standards_system": "Name of the standards system",
            "topic_categories": {{
                "category-key": {{
                    "description": "Category description with standards references",
                    "source_topics": ["career-planning", "tax-planning", etc.],
                    "state_standards": ["specific standards codes"]
                }}
            }}
        }}
        
        Use these source topics to map from:
        - career-planning
        - tax-planning
        - financial-services
        - banking-tools
        - saving-investing
        - retirement-planning
        - credit-borrowing
        - credit-cards-consumer-protection
        - fraud-protection
        - housing-decisions
        - insurance-risk-management
        - entertainment-gambling
        - debt-management
        - charitable-giving
        - career-readiness
        
        Alignment content:
        {alignment_content[:8000]}  # Limit content to avoid token limits
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text.strip()
            
            # Clean up any markdown formatting
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            mapping = json.loads(content.strip())
            logger.info(f"Successfully extracted standards mapping for {state_name}")
            return mapping
            
        except Exception as e:
            logger.error(f"Error extracting standards mapping for {state_name}: {e}")
            return self.get_fallback_mapping(state_name)
    
    def get_fallback_mapping(self, state_name):
        """Provide fallback mapping if AI extraction fails."""
        return {
            "state_name": state_name,
            "standards_system": f"{state_name} Academic Standards",
            "topic_categories": {
                "career-and-education": {
                    "description": f"{state_name} Career and Education Standards",
                    "source_topics": ["career-planning", "career-readiness"],
                    "state_standards": ["Career-1", "Career-2"]
                },
                "financial-planning": {
                    "description": f"{state_name} Financial Planning Standards", 
                    "source_topics": ["tax-planning", "saving-investing", "retirement-planning"],
                    "state_standards": ["Finance-1", "Finance-2"]
                },
                "banking-and-credit": {
                    "description": f"{state_name} Banking and Credit Standards",
                    "source_topics": ["banking-tools", "credit-borrowing", "credit-cards-consumer-protection"],
                    "state_standards": ["Banking-1", "Banking-2"]
                },
                "consumer-protection": {
                    "description": f"{state_name} Consumer Protection Standards",
                    "source_topics": ["fraud-protection", "insurance-risk-management"],
                    "state_standards": ["Consumer-1", "Consumer-2"]
                },
                "specialized-topics": {
                    "description": f"{state_name} Specialized Financial Topics",
                    "source_topics": ["housing-decisions", "entertainment-gambling", "debt-management", "charitable-giving"],
                    "state_standards": ["Special-1", "Special-2"]
                }
            }
        }
    
    def localize_html(self, file_path, state_data):
        """Resolve federal + state figures for one HTML file.

        Delegates to figure_resolver.resolve_file, which:
          * updates standalone old-year FEDERAL literals to the current year from
            federal_figures.json (holding computed/bracket/contribution files untouched);
          * resolves {{STATE_*}} tokens from {state}.json, rendering a flagged placeholder
            for any null backing field (never an Oklahoma value, never a guess);
          * localizes branding to the target state.

        Returns (localized_html, per_file_report).
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return fr.resolve_file(content, state_data, self.federal)
    
    def create_state_readme(self, state_dir, metadata, standards_mapping):
        """Create comprehensive README for state resources."""
        
        state_name = standards_mapping["state_name"]
        standards_system = standards_mapping["standards_system"]
        topic_categories = standards_mapping["topic_categories"]
        
        readme_content = f"""# {state_name} Financial Literacy Resources
## PFL Academy Free Educational Materials

### 🎓 Overview
This directory contains {metadata['total_resources']} professionally sanitized financial literacy resources specifically organized for {state_name} {standards_system} alignment.

### 📚 {state_name} Standards Organization

#### Standards Coverage:
"""
        
        for category_key, category_info in topic_categories.items():
            resource_count = len([r for r in metadata['resources'] if r['state_category'] == category_key])
            readme_content += f"""
**{category_info['description']}**
- Directory: `{category_key}/`
- State Standards: {', '.join(category_info['state_standards'])}
- Resources Available: {resource_count}
"""
        
        readme_content += f"""

### 🎯 {state_name} Education Benefits

#### For {state_name} Educators:
- **Standards Compliance**: All resources mapped to {state_name} {standards_system}
- **Professional Quality**: Sanitized content with {state_name}-specific branding
- **Print-Ready Format**: HTML resources optimized for classroom printing
- **Comprehensive Coverage**: Spans all major financial literacy topics

#### For {state_name} Students:
- **Age-Appropriate Content**: Designed for grades 9-12
- **Practical Applications**: Real-world financial scenarios
- **Skill Building**: Progressive learning objectives
- **Career Readiness**: Preparation for post-secondary financial decisions

### 📋 Implementation Guide

#### For {state_name} Teachers:
1. **Select Resources** by {state_name} standards alignment
2. **Download & Print** HTML resources for classroom use
3. **Integrate** with existing economics curriculum
4. **Assess** student learning with built-in evaluation tools

#### Recommended Usage:
- **Semester Course**: Use 2-3 resources per standard
- **Year-Long Course**: Comprehensive coverage across all categories
- **Supplemental Materials**: Enhance existing financial literacy units
- **Professional Development**: Reference materials for teacher training

### 📊 Metadata & Tracking
- **Resource Metadata**: `{state_name.lower()}-resource-metadata.json`
- **Original Chapter Mapping**: Preserved for curriculum alignment
- **State Standards Mapping**: Detailed in metadata file
- **Quality Assurance**: All content professionally sanitized

### 🤝 {state_name} Education Partnership Ready
These resources are prepared for:
- **{state_name} Department of Education** submission
- **Regional Education Service Centers** distribution
- **School District** implementation
- **Teacher Professional Development** programs

### 📞 Support & Additional Resources
- **Full Curriculum**: Available at pflacademy.co
- **Professional Development**: {state_name} educator training available
- **Technical Support**: Implementation assistance provided
- **Partnership Opportunities**: Contact partnerships@pflacademy.co

---
*Prepared specifically for {state_name} educators in alignment with {standards_system}*
*All resources professionally sanitized and {state_name}-branded for classroom use*

**Generated**: {datetime.now().strftime('%B %Y')} | **Resources**: {metadata['total_resources']} | **Standards**: {state_name}-Aligned
"""
        
        readme_path = state_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Created comprehensive {state_name} README.md")
    
    def process_state(self, state_name):
        """Process a single state with standards alignment (full pipeline)."""

        slug = self.state_name_to_slug(state_name)
        state_data = fr.load_state(slug)
        if state_data is None:
            logger.warning(f"No state-data/states/{slug}.json — skipping {state_name}")
            return 0
        missing, _ = fr.state_completeness(state_data)
        if missing:
            logger.warning(f"{state_name} incomplete (missing {missing}) — skipping")
            return 0

        logger.info(f"🏛️ Processing {state_name} resources...")

        # Create state directory
        state_dir = self.output_base_dir / f"{slug}-aligned-resources"
        state_dir.mkdir(exist_ok=True)

        # Get state alignment content
        alignment_content = self.get_state_alignment_content(state_name)
        if not alignment_content:
            logger.warning(f"No alignment content found for {state_name}, using fallback")
        
        # Extract standards mapping using Claude
        standards_mapping = self.extract_standards_mapping(state_name, alignment_content)
        
        # Create topic directories
        topic_categories = standards_mapping["topic_categories"]
        for category_key in topic_categories.keys():
            (state_dir / category_key).mkdir(exist_ok=True)
        
        # Create metadata tracking
        resource_metadata = {
            "state": state_name,
            "standards": standards_mapping["standards_system"],
            "sanitized_date": datetime.now().strftime('%Y-%m-%d'),
            "total_resources": 0,
            "resources": [],
            "standards_organization": standards_mapping
        }
        
        total_processed = 0
        
        # Process each Oklahoma topic directory
        for oklahoma_topic_dir in self.base_oklahoma_dir.iterdir():
            if not oklahoma_topic_dir.is_dir() or oklahoma_topic_dir.name.startswith('.'):
                continue
            
            topic_name = oklahoma_topic_dir.name
            
            # Find appropriate state category for this topic
            target_category = None
            for category_key, category_info in topic_categories.items():
                if topic_name in category_info["source_topics"]:
                    target_category = category_key
                    break
            
            # Default to first category if no specific match
            if not target_category:
                target_category = list(topic_categories.keys())[0]
            
            # Process each resource file
            for resource_file in oklahoma_topic_dir.glob("*.html"):
                # Extract metadata from filename
                filename_parts = resource_file.name.split('_', 1)
                if len(filename_parts) == 2:
                    chapter_id = filename_parts[0]
                    original_name = filename_parts[1]
                else:
                    chapter_id = "unknown"
                    original_name = resource_file.name
                
                # Resolve federal + state figures (replaces the old cosmetic sanitize)
                sanitized_content, _rep = self.localize_html(resource_file, state_data)

                # Create state-branded filename
                clean_name = original_name.replace('.html', '').replace('_', ' ').title().replace(' ', '_')
                sanitized_filename = f"{state_name}_{clean_name}.html"
                
                # Write sanitized file to state category
                target_dir = state_dir / target_category
                output_path = target_dir / sanitized_filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(sanitized_content)
                
                # Track in metadata
                resource_info = {
                    "filename": sanitized_filename,
                    "original_chapter": chapter_id,
                    "original_name": original_name,
                    "state_category": target_category,
                    "state_standards": topic_categories[target_category]["state_standards"],
                    "source_topic": topic_name
                }
                
                resource_metadata["resources"].append(resource_info)
                total_processed += 1
        
        resource_metadata["total_resources"] = total_processed
        
        # Save metadata file
        metadata_path = state_dir / f"{state_name.lower()}-resource-metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(resource_metadata, f, indent=2)
        
        # Create state README
        self.create_state_readme(state_dir, resource_metadata, standards_mapping)
        
        logger.info(f"✅ {state_name} complete: {total_processed} resources processed")
        return total_processed
    
    # ------------------------------------------------------------------
    # Figure-resolution slice (no AI, no network) — the verifiable deliverable.
    # ------------------------------------------------------------------
    def process_state_figures(self, state_slug, out_root, write=True):
        """Resolve figures for one state across the whole corpus, preserving the source
        topic-directory layout. Returns an aggregate report dict. No AI standards-mapping."""
        state_data = fr.load_state(state_slug)
        if state_data is None:
            return {"state": state_slug, "error": "no state-data json"}
        missing, prop_null = fr.state_completeness(state_data)

        agg = {"state": state_data["state_name"], "slug": state_slug,
               "incomplete_fields": missing, "property_rate_null": prop_null,
               "files": 0, "federal_updated": [], "federal_review": [],
               "state_placeholders": 0, "federal_substitutions": 0}

        state_out = Path(out_root) / f"{state_slug}-aligned-resources"
        for topic_dir in sorted(self.base_oklahoma_dir.iterdir()):
            if not topic_dir.is_dir() or topic_dir.name.startswith('.'):
                continue
            for src in sorted(topic_dir.glob("*.html")):
                html, rep = self.localize_html(src, state_data)
                agg["files"] += 1
                if rep["federal_status"] == "updated":
                    agg["federal_updated"].append(str(src.relative_to(self.base_oklahoma_dir)))
                    agg["federal_substitutions"] += len(rep["federal_applied"])
                elif rep["federal_status"] == "review":
                    agg["federal_review"].append(str(src.relative_to(self.base_oklahoma_dir)))
                agg["state_placeholders"] += sum(1 for t in rep["state_tokens"]
                                                 if t["placeholder"])
                if write:
                    dest = state_out / topic_dir.name / src.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(html, encoding="utf-8")
        return agg

    def run_dry_run(self, states=None, out_root=None):
        """Figure resolution + report for the given states (default NC/KY/TX). No API."""
        out_root = Path(out_root) if out_root else (fr.REPO_ROOT / "free-resources-dryrun")
        slugs = states or ["north-carolina", "kentucky", "texas"]
        print("=" * 72)
        print(f"DRY-RUN — figure resolution over {len(slugs)} state(s), no AI/network")
        print(f"Output: {out_root}")
        print("=" * 72)
        for slug in slugs:
            agg = self.process_state_figures(slug, out_root)
            if "error" in agg:
                print(f"\n{slug}: ERROR {agg['error']}")
                continue
            print(f"\n{agg['state']} ({slug}):")
            print(f"  files localized:              {agg['files']}")
            print(f"  federal files auto-updated:   {len(agg['federal_updated'])} "
                  f"({agg['federal_substitutions']} substitutions from federal_figures.json)")
            print(f"  federal files held for review:{len(agg['federal_review'])}")
            print(f"  state null-field placeholders:{agg['state_placeholders']} "
                  f"(property_tax_effective_rate null: {agg['property_rate_null']})")
            if agg["incomplete_fields"]:
                print(f"  INCOMPLETE critical fields:   {agg['incomplete_fields']}")
        print(f"\nProcessed-state count available via `--report`.")
        return out_root


def main():
    ap = argparse.ArgumentParser(description="PFL Academy multi-state free-PDF generator")
    ap.add_argument("--dry-run", action="store_true",
                    help="Figure resolution + report only (no AI/network). The verifiable "
                         "slice. Writes to free-resources-dryrun/.")
    ap.add_argument("--report", action="store_true",
                    help="Corpus-wide federal currency + state completeness report.")
    ap.add_argument("--full", action="store_true",
                    help="Full pipeline incl. AI standards-mapping (needs ANTHROPIC_API_KEY).")
    ap.add_argument("--states", nargs="*", default=None,
                    help="State slugs (e.g. north-carolina kentucky texas). Default NC/KY/TX "
                         "for --dry-run; all 36 for --full.")
    args = ap.parse_args()

    if args.report:
        fr.run_report()
        return

    gen = StateResourceGenerator()

    if args.dry_run or not args.full:
        gen.run_dry_run(states=args.states)
        return

    # Full pipeline
    slugs = args.states or gen.state_slugs
    print("PFL Academy Multi-State Resource Generator — FULL")
    print(f"Processing {len(slugs)} states with a canonical {{state}}.json")
    total = 0
    for slug in slugs:
        name = fr.load_state(slug)["state_name"] if fr.load_state(slug) else slug
        try:
            total += gen.process_state(name)
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
    print(f"\nTotal resources created: {total}")
    print(f"Output: {gen.output_base_dir}")


if __name__ == "__main__":
    main()