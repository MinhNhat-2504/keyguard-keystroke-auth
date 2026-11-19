"""Paired offline profile contamination study, no requests to real services."""
import numpy as np
from keyguard.model import build_profile, profile_z

POLICIES = ('static', 'accept', 'fallback', 'verified_only')


def should_update(policy, genuine, accepted):
    if policy not in POLICIES:
        raise ValueError('Unknown policy')
    return (policy=='accept' and accepted) or (policy=='fallback' and (genuine or accepted)) or (
        policy=='verified_only' and genuine)


def run_stream(enrollment, genuine, attacks, probes, cfg, policy, inject=True, every=5):
    """One predetermined attack after every 5 genuine; probes never update.

    fallback assumes genuine always pass extra verification; accepted impostors
    still contaminate this policy. verified_only is an ideal independent verifier
    for EVERY update, not an implemented OTP guarantee.
    """
    if policy not in POLICIES or every<1 or len(attacks)!=len(genuine)//every:
        raise ValueError('Invalid policy or stream schedule')
    X=np.array(enrollment,copy=True)
    labels=np.zeros(len(X),dtype=bool)
    profile=build_profile(X,cfg)
    tau=cfg['threshold']
    history=[]
    rejects=accepted_attacks=attack_index=peak_contamination=0
    def checkpoint(step):
        scores=profile_z(profile,probes)
        history.append({'genuine_seen':step,'probe_trials':len(scores),
                        'probe_accepted':int(np.count_nonzero(scores<=tau)),
                        'contaminated_rows':int(labels.sum()),'profile_rows':len(labels)})
    def update(sample,is_attack):
        nonlocal X,labels,profile,peak_contamination
        X=np.vstack([X,sample])[-cfg['window']:]
        labels=np.r_[labels,is_attack][-cfg['window']:]
        peak_contamination=max(peak_contamination,int(labels.sum()))
        profile=build_profile(X,cfg)
    checkpoint(0)
    for step,sample in enumerate(genuine,1):
        accepted=bool(profile_z(profile,sample)[0]<=tau)
        rejects+=not accepted
        if should_update(policy,True,accepted):
            update(sample,False)
        if step%every==0:
            attack=attacks[attack_index]
            attack_index+=1
            if inject:
                admitted=bool(profile_z(profile,attack)[0]<=tau)
                accepted_attacks+=admitted
                if should_update(policy,False,admitted):
                    update(attack,True)
        if step%50==0 or step==len(genuine):
            checkpoint(step)
    return {'genuine_trials':len(genuine),'genuine_rejected':int(rejects),
            'attack_trials':len(attacks) if inject else 0,
            'attacks_accepted':int(accepted_attacks),'checkpoints':history,
            'final_contaminated_rows':int(labels.sum()),
            'peak_contaminated_rows_all_updates':peak_contamination,
            'peak_contaminated_rows_at_checkpoints':max(h['contaminated_rows'] for h in history)}
