import numpy as np

import generals.game as game
import generals.utils as utils
import itertools

def get_game(map_name=None):
    if map_name:
        map = utils.map_from_file(map_name)
    else:
        map = utils.map_from_generator(
            grid_size=10,
            mountain_density=0.1,
            city_density=0.1,
            general_positions=[[3, 3], [1, 3]]
        )
    return game.Game(map, ['red', 'blue'])

def test_grid_creation():
    """
    For given configuration, we should get grid of given size.
    """
    for _ in range(10):
        game = get_game()
        assert game.grid_size == 10
        assert game.map.shape == (10, 10)

        # mountain and city should be disjoint
        assert np.logical_and(game.channels['mountain'], game.channels['city']).sum() == 0

        owners = ['neutral'] + game.agents
        # for every pair of agents, the ownership channels should be disjoint
        pairs = itertools.combinations(owners, 2)
        for pair in pairs:
            ownership_a = game.channels[f'ownership_{pair[0]}']
            ownership_b = game.channels[f'ownership_{pair[1]}']
            assert np.logical_and(ownership_a, ownership_b).sum() == 0

        # but union of all ownerships should be equal to passable channel
        ownerships = [game.channels[f'ownership_{owner}'] for owner in owners]
        union = np.logical_or.reduce(ownerships)
        assert (union == game.channels['passable']).all()

    

def test_channel_to_indices():
    """
    For given channel, we should get indices of cells that are 1.
    """
    game = get_game()

    channel = np.array([
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ])
    reference = np.array([(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)])
    indices = game.channel_to_indices(channel)
    assert (indices == reference).all()

    channel = np.array([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ])
    reference = np.empty((0, 2))
    indices = game.channel_to_indices(channel)
    assert (indices == reference).all()

def test_visibility_channel():
    """
    For given ownership mask, we should get visibility mask.
    """
    dummy_game = get_game()

    ownership = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ])
    reference = np.array([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ])
    visibility = dummy_game.visibility_channel(ownership)
    assert (visibility == reference).all()

    ownership = np.array([
        [0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1]
    ])
    reference = np.array([
        [1, 1, 1, 0 ,0],
        [1, 1, 1, 0 ,0],
        [1, 1, 1, 1 ,1],
        [1, 1, 1, 1 ,1],
        [0, 0, 0, 1 ,1]
    ])
    visibility = dummy_game.visibility_channel(ownership)
    assert (visibility == reference).all()

def test_action_mask():
    """
    For given ownership mask and passable mask, we should get NxNx4 mask of valid actions.
    """
    game = get_game()
    game.grid_size = 4
    game.channels['passable'] = np.array([
        [1, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 0, 1, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)

    game.channels['ownership_red'] = np.array([
        [0, 0, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 1, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)
    reference = np.array([
        # UP
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 0, 0, 0],
        ],
        # DOWN
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        # LEFT
        [
            [0, 0, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        # RIGHT
        [
            [0, 0, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
    ], dtype=np.float32)

    action_mask = game.action_mask('red')
    assert (action_mask[:, :, 0] == reference[0]).all()
    assert (action_mask[:, :, 1] == reference[1]).all()
    assert (action_mask[:, :, 2] == reference[2]).all()
    assert (action_mask[:, :, 3] == reference[3]).all()


def test_observations():
    """
    For given actions, we should get new state of the game.
    """
    game = get_game(map_name='test_map')
    game.channels['ownership_red'] = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    game.channels['ownership_blue'] = np.array([
        [1, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    game.channels['army'] = np.array([
        [3, 0, 0, 0],
        [0, 3, 6, 2],
        [1, 9, 5, 0],
        [0, 0, 5, 8],
    ], dtype=np.float32)
    game.channels['ownership_neutral'] = np.array([
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)

    ############
    # TEST RED #
    ############
    red_observation = game._agent_observation('red')
    reference_opponent_ownership = np.array([
        [0, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (red_observation['ownership_opponent'] == reference_opponent_ownership).all()

    reference_neutral_ownership = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)
    assert (red_observation['ownership_neutral'] == reference_neutral_ownership).all()

    reference_ownership = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    assert (red_observation['ownership'] == reference_ownership).all()

    # union of all ownerships should be zero
    assert (
        np.logical_and.reduce([
            red_observation['ownership_opponent'],
            red_observation['ownership_neutral'],
            red_observation['ownership']
        ])
    ).sum() == 0


    reference_army = np.array([
        [0, 0, 0, 0],
        [0, 3, 6, 2],
        [1, 9, 5, 0],
        [0, 0, 5, 8],
    ], dtype=np.float32)
    assert (red_observation['army'] == reference_army).all()

    #############
    # TEST BLUE #
    #############
    blue_observation = game._agent_observation('blue')
    reference_opponent_ownership = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (blue_observation['ownership_opponent'] == reference_opponent_ownership).all()

    reference_neutral_ownership = np.array([
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (blue_observation['ownership_neutral'] == reference_neutral_ownership).all()

    reference_ownership = np.array([
        [1, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (blue_observation['ownership'] == reference_ownership).all()

    reference_army = np.array([
        [3, 0, 0, 0],
        [0, 3, 6, 2],
        [1, 9, 5, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (blue_observation['army'] == reference_army).all()

    # union of all ownerships should be zero
    assert (
        np.logical_and.reduce([
            blue_observation['ownership_opponent'],
            blue_observation['ownership_neutral'],
            blue_observation['ownership']
        ])
    ).sum() == 0


def test_game_step():
    """
    Test three moves from this situation
    """
    game = get_game(map_name='test_map')
    game.channels['ownership_red'] = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    game.channels['ownership_blue'] = np.array([
        [1, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    game.channels['army'] = np.array([
        [3, 0, 0, 0],
        [0, 3, 6, 2],
        [1, 9, 5, 0],
        [0, 0, 5, 8],
    ], dtype=np.float32)
    game.channels['ownership_neutral'] = np.array([
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)

    #############################################################################################################
    # red moves from (2, 1) UP (captures blue square), blue moves from (1, 2) DOWN, (doesnt capture red square) #
    #############################################################################################################
    moves = {
        'red': np.array([2, 1, 0, 0]),
        'blue': np.array([1, 2, 1, 0])
    }
    game.step(moves)
    reference_army = np.array([
        [3, 0, 0, 0],
        [0, 5, 1, 2],
        [1, 1, 0, 0],
        [0, 0, 5, 8],
    ], dtype=np.float32)
    assert (game.channels['army'] == reference_army).all()

    reference_ownership_red = np.array([
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    assert (game.channels['ownership_red'] == reference_ownership_red).all()
    
    reference_ownership_blue = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_blue'] == reference_ownership_blue).all()

    reference_ownership_neutral = np.array([
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_neutral'] == reference_ownership_neutral).all()

    reference_total_army_red = 20
    stats = game.get_infos()
    assert stats['red']['army'] == reference_total_army_red

    reference_total_army_blue = 6
    assert stats['blue']['army'] == reference_total_army_blue

    reference_total_army_land = 6
    assert stats['red']['land'] == reference_total_army_land

    reference_total_army_land = 3
    assert stats['blue']['land'] == reference_total_army_land

    #####################################################################################
    # Now red moves from (2, 1) DOWN (should not move) and blue moves from (0, 0) RIGHT #
    #####################################################################################
    moves = {
        'red': np.array([2, 1, 1, 0]),
        'blue': np.array([0, 0, 3, 0])
    }
    game.step(moves)

    # this is second move, so army increments in base
    reference_army = np.array([
        [1, 2, 0, 0],
        [0, 5, 1, 3],
        [1, 1, 0, 0],
        [0, 0, 5, 9],
    ], dtype=np.float32)
    assert (game.channels['army'] == reference_army).all()

    reference_ownership_red = np.array([
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    assert (game.channels['ownership_red'] == reference_ownership_red).all()

    reference_ownership_blue = np.array([
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_blue'] == reference_ownership_blue).all()

    reference_ownership_neutral = np.array([
        [0, 0, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_neutral'] == reference_ownership_neutral).all()

    reference_total_army_red = 21
    stats = game.get_infos()
    assert stats['red']['army'] == reference_total_army_red

    reference_total_army_blue = 7
    assert stats['blue']['army'] == reference_total_army_blue

    reference_total_army_land = 6
    assert stats['red']['land'] == reference_total_army_land

    reference_total_army_land = 4
    assert stats['blue']['land'] == reference_total_army_land

    #####################################################################################
    # Red sends half army from (3, 3) LEFT and blue sends half army from (1, 3) LEFT    #
    #####################################################################################
    moves = {
        'red': np.array([3, 3, 2, 1]),
        'blue': np.array([1, 3, 2, 1])
    }
    game.step(moves)
    reference_army = np.array([
        [1, 2, 0, 0],
        [0, 5, 2, 2],
        [1, 1, 0, 0],
        [0, 0, 9, 5],
    ], dtype=np.float32)
    assert (game.channels['army'] == reference_army).all()

    reference_ownership_red = np.array([
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)
    assert (game.channels['ownership_red'] == reference_ownership_red).all()

    reference_ownership_blue = np.array([
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_blue'] == reference_ownership_blue).all()

    reference_ownership_neutral = np.array([
        [0, 0, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)
    assert (game.channels['ownership_neutral'] == reference_ownership_neutral).all()

    reference_total_army_red = 21
    stats = game.get_infos()
    assert stats['red']['army'] == reference_total_army_red

    reference_total_army_blue = 7
    assert stats['blue']['army'] == reference_total_army_blue

    reference_total_army_land = 6
    assert stats['red']['land'] == reference_total_army_land

    reference_total_army_land = 4
    assert stats['blue']['land'] == reference_total_army_land

    ##############################
    # Test global army increment #
    ##############################
    game.time = 50
    game._global_game_update()
    print(game.channels['army'])
    reference_army = np.array([
        [2, 3, 0, 0],
        [0, 6, 3, 4],
        [2, 2, 1, 0],
        [0, 0, 10, 7],
    ], dtype=np.float32)
    assert (game.channels['army'] == reference_army).all()

    reference_total_army_red = 28
    stats = game.get_infos()
    assert stats['red']['army'] == reference_total_army_red

    reference_total_army_blue = 12
    assert stats['blue']['army'] == reference_total_army_blue

    reference_total_army_land = 6
    assert stats['red']['land'] == reference_total_army_land

    reference_total_army_land = 4
    assert stats['blue']['land'] == reference_total_army_land


def test_end_of_game():
    game = get_game(map_name='test_map')
    game.general_positions = {
        'red': [3, 3],
        'blue': [1, 3]
    }
    game.channels['ownership_red'] = np.array([
        [0, 0, 0, 0],
        [0, 0, 1, 0],
        [1, 1, 1, 0],
        [0, 0, 1, 1],
    ], dtype=np.float32)

    game.channels['ownership_blue'] = np.array([
        [1, 1, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=np.float32)

    game.channels['army'] = np.array([
        [3, 2, 2, 0],
        [0, 3, 6, 2],
        [1, 9, 5, 0],
        [0, 0, 5, 8],
    ], dtype=np.float32)

    game.channels['ownership_neutral'] = np.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.float32)

    moves = {
        'red': np.array([2, 1, 0, 0]), # random move
        'blue': np.array([0, 1, 1, 0]) # random move
    }
    game.step(moves)

    # Neither should win
    assert not game.agent_won('red')
    assert not game.agent_won('blue')
    assert not game.is_done()


    moves = {
        'red': np.array([1, 2, 3, 0]), # random move
        'blue': np.array([0, 0, 3, 0]) # move to blues general
    }
    game.step(moves)

    # Red should win
    assert game.agent_won('red')

    # Blue should be dead
    assert not game.agent_won('blue')

    # Game should be done
    assert game.is_done()

